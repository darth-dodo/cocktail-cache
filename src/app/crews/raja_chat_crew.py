"""Raja Chat Crew for conversational cocktail interactions.

This crew provides a personality-rich chat experience with Raja,
a bartender from Bombay who offers cocktail advice through natural
conversation.

The crew maintains conversation context and integrates with the
existing drink data services for accurate recommendations.
"""

import json
import logging
import re
import time
import uuid
from datetime import datetime

from crewai import Crew, Process, Task

from src.app.agents.raja_bartender import create_raja_bartender
from src.app.models.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSession,
    DrinkReference,
    MessageIntent,
    MessageRole,
    RajaChatOutput,
)
from src.app.services.data_loader import load_all_drinks

logger = logging.getLogger(__name__)

# In-memory session store (use Redis in production)
_chat_sessions: dict[str, ChatSession] = {}


def get_or_create_session(
    session_id: str | None,
    cabinet: list[str] | None = None,
    skill_level: str | None = None,
    drink_type: str | None = None,
) -> ChatSession:
    """Get existing session or create a new one.

    Args:
        session_id: Existing session ID or None for new session.
        cabinet: User's cabinet ingredients (for new/update).
        skill_level: User's skill level (for new/update).
        drink_type: Preferred drink type (for new/update).

    Returns:
        ChatSession instance.
    """
    if session_id and session_id in _chat_sessions:
        session = _chat_sessions[session_id]
        session.last_active = datetime.utcnow()

        # Update context if provided
        if cabinet is not None:
            session.cabinet = cabinet
        if skill_level is not None:
            session.skill_level = skill_level
        if drink_type is not None:
            session.drink_type_preference = drink_type

        return session

    # Create new session
    new_session = ChatSession(
        session_id=str(uuid.uuid4()),
        cabinet=cabinet or [],
        skill_level=skill_level or "intermediate",
        drink_type_preference=drink_type or "cocktail",
    )

    # Add Raja's greeting as first message
    greeting = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.RAJA,
        content=(
            "Arrey yaar, welcome! Raja here - learned from best in the business. "
            "Tell me, what's the mood today? Celebrating something or just relaxing?\n\n"
            "⚠️ *Quick note: I'm an AI - please verify recipes before mixing!*"
        ),
        intent=None,
    )
    new_session.history.add_message(greeting)

    _chat_sessions[new_session.session_id] = new_session
    logger.info(f"Created new chat session: {new_session.session_id}")

    return new_session


def _get_makeable_drinks(cabinet: list[str], drink_type: str) -> list[dict]:
    """Get drinks makeable with the user's cabinet.

    Args:
        cabinet: List of ingredient IDs.
        drink_type: "cocktail", "mocktail", or "both".

    Returns:
        List of drink dictionaries with id, name, tagline.
    """
    all_drinks = load_all_drinks()
    cabinet_set = {ing.lower() for ing in cabinet}

    makeable = []
    for drink in all_drinks:
        # Filter by drink type
        if drink_type == "cocktail" and drink.is_mocktail:
            continue
        if drink_type == "mocktail" and not drink.is_mocktail:
            continue

        # Check if all ingredients are available
        drink_ingredients = {ing.item.lower() for ing in drink.ingredients}
        if drink_ingredients.issubset(cabinet_set):
            makeable.append(
                {
                    "id": drink.id,
                    "name": drink.name,
                    "tagline": drink.tagline,
                    "difficulty": drink.difficulty,
                }
            )

    return makeable


def _format_drinks_for_prompt(drinks: list[dict], limit: int = 10) -> str:
    """Format drinks list for inclusion in prompt."""
    if not drinks:
        return "No drinks currently makeable with their cabinet."

    lines = []
    for drink in drinks[:limit]:
        lines.append(f"- {drink['name']}: {drink['tagline']} ({drink['difficulty']})")

    if len(drinks) > limit:
        lines.append(f"... and {len(drinks) - limit} more drinks")

    return "\n".join(lines)


def _get_drink_by_id(drink_id: str) -> dict | None:
    """Get a drink by its ID."""
    all_drinks = load_all_drinks()
    for drink in all_drinks:
        if drink.id == drink_id:
            return {
                "id": drink.id,
                "name": drink.name,
                "tagline": drink.tagline,
            }
    return None


def _get_all_drink_ids() -> set[str]:
    """Get a set of all drink IDs in our database."""
    all_drinks = load_all_drinks()
    return {drink.id for drink in all_drinks}


def create_raja_chat_crew(session: ChatSession, user_message: str) -> Crew:
    """Create the Raja Chat Crew for conversational interactions.

    The crew uses a single Raja Bartender agent that receives:
    - Conversation history for context
    - User's cabinet and preferences
    - Available drink data for recommendations

    Args:
        session: The chat session with history and user context.
        user_message: The user's current message.

    Returns:
        A configured CrewAI Crew instance.
    """
    logger.info(f"Creating Raja chat crew for session {session.session_id}")

    # Create Raja agent without tools - data is injected via prompts
    raja = create_raja_bartender(tools=[])

    # Get available drinks for context
    makeable_drinks = []
    available_drinks_text = "No cabinet set up yet."
    if session.cabinet:
        makeable_drinks = _get_makeable_drinks(
            cabinet=session.cabinet,
            drink_type=session.drink_type_preference,
        )
        if makeable_drinks:
            available_drinks_text = _format_drinks_for_prompt(makeable_drinks, limit=10)

    # Format conversation history
    history_text = session.history.format_for_prompt(last_n=8)

    # Get all drink IDs from our database for validation
    all_drink_ids = _get_all_drink_ids()
    drink_ids_sample = sorted(all_drink_ids)[:50]  # Sample for prompt context

    # Build the chat task
    chat_task = Task(
        description=f"""You are Raja, responding to a customer in your bar. Stay in character!

CONVERSATION SO FAR:
{history_text}

CUSTOMER'S LATEST MESSAGE:
{user_message}

CUSTOMER'S BAR CABINET:
{len(session.cabinet)} bottles: {", ".join(session.cabinet[:15])}{"..." if len(session.cabinet) > 15 else ""}

DRINKS THEY CAN MAKE:
{available_drinks_text}

OUR DRINK DATABASE (sample of {len(all_drink_ids)} drinks):
{", ".join(drink_ids_sample)}{"..." if len(all_drink_ids) > 50 else ""}

CUSTOMER INFO:
- Skill Level: {session.skill_level}
- Drink Preference: {session.drink_type_preference}
- Current Mood: {session.current_mood or "not yet determined"}

INSTRUCTIONS:
1. BE SNAPPY! 2-3 sentences max. Get to the point with warmth. No long monologues.
2. Use respectful Hindi: "yaar", "bhai", "acha", "bilkul", "zaroor", "kya baat hai". Keep it friendly.
3. For recommendations: Quick mood check if needed, then your pick. No rambling.
4. CRITICAL: Only share SECOND-HAND stories. Say "I heard...", "They say...", "Legend has it...", "An old regular once told me...". NEVER first-person experiences like "I remember when I..." or "Back when I served...".
5. Be encouraging but concise. Warm and wise, not lengthy lectures.
6. If they need ingredients, tell them kindly - "Yaar, grab some X and you're all set."

CRITICAL - DRINK RECOMMENDATIONS:
- If recommending a drink that IS in our database (check the drink IDs above), use "recommended_drink_id" with the exact ID.
- If recommending a drink that is NOT in our database, you MUST provide the FULL RECIPE in "special_recipe" field.
  This is "Raja's Special from Memory" - a drink you know but we don't have in our collection.
  Include: name, tagline, ingredients (with amounts like "2 oz bourbon"), method (step-by-step), glassware, garnish, and your personal tip.

IMPORTANT: Return a JSON object matching the RajaChatOutput schema.""",
        expected_output="""A JSON object with structure:
{{
  "response": "Raja's conversational response with personality",
  "detected_intent": "recommendation_request|recipe_question|general_chat|greeting|technique_question|ingredient_question|cabinet_update|feedback|goodbye",
  "detected_mood": "relaxed|celebratory|contemplative|adventurous|tired|social|romantic|null",
  "drinks_mentioned": ["drink-id-1", "drink-id-2"],
  "ingredients_mentioned": ["bourbon", "sweet-vermouth"],
  "recommendation_made": true,
  "recommended_drink_id": "manhattan",
  "suggested_follow_up": "Shall I tell you the story of how the Manhattan was invented?",
  "special_recipe": null
}}

If drink is NOT in our database, include special_recipe:
{{
  "response": "Arrey yaar, let me share a special one from my memory...",
  "recommendation_made": true,
  "recommended_drink_id": null,
  "special_recipe": {{
    "name": "Drink Name",
    "tagline": "Short description",
    "ingredients": ["2 oz bourbon", "1 oz sweet vermouth", "2 dashes bitters"],
    "method": ["Add ingredients to mixing glass", "Stir with ice for 30 seconds", "Strain into chilled coupe"],
    "glassware": "coupe",
    "garnish": "cherry",
    "tip": "Raja's personal tip for making this drink perfect"
  }}
}}""",
        agent=raja,
        output_pydantic=RajaChatOutput,
    )

    return Crew(
        agents=[raja],
        tasks=[chat_task],
        process=Process.sequential,
        verbose=False,
    )


def _parse_raja_output(result) -> RajaChatOutput:
    """Parse crew result into structured RajaChatOutput."""
    # Try pydantic output first
    if hasattr(result, "pydantic") and isinstance(result.pydantic, RajaChatOutput):
        return result.pydantic

    # Fallback: parse from raw
    raw_output = str(result.raw) if hasattr(result, "raw") else str(result)

    try:
        json_match = re.search(r"\{[\s\S]*\}", raw_output)
        if json_match:
            data = json.loads(json_match.group())
            return RajaChatOutput(**data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse Raja output: {e}")

    # Final fallback
    return RajaChatOutput(
        response=raw_output
        if raw_output
        else "Arrey, something went wrong! Let me try again, yaar.",
        detected_intent=MessageIntent.GENERAL_CHAT,
    )


def _get_suggested_action(output: RajaChatOutput) -> str | None:
    """Determine suggested UI action based on Raja's response."""
    if output.recommendation_made and output.recommended_drink_id:
        return "view_recipe"
    if output.detected_intent == MessageIntent.CABINET_UPDATE:
        return "update_cabinet"
    if output.detected_intent == MessageIntent.RECOMMENDATION_REQUEST:
        return "show_recommendations"
    return None


def run_raja_chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and get Raja's response.

    This function:
    1. Gets or creates the chat session
    2. Adds the user message to history
    3. Runs the Raja crew to generate response
    4. Updates session with Raja's response
    5. Returns structured response with metadata

    Args:
        request: The chat request with message and context.

    Returns:
        ChatResponse with Raja's message and extracted entities.
    """
    start_time = time.perf_counter()

    # Get or create session
    session = get_or_create_session(
        session_id=request.session_id,
        cabinet=request.cabinet,
        skill_level=request.skill_level,
        drink_type=request.drink_type,
    )

    logger.info(
        f"Processing chat for session {session.session_id}: "
        f"message_length={len(request.message)}"
    )

    # Add user message to history
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        content=request.message,
    )
    session.history.add_message(user_message)

    # Create and run crew
    crew = create_raja_chat_crew(session, request.message)

    crew_start = time.perf_counter()
    result = crew.kickoff()
    crew_elapsed_ms = (time.perf_counter() - crew_start) * 1000
    logger.debug(f"Raja crew completed in {crew_elapsed_ms:.2f}ms")

    # Parse output
    raja_output = _parse_raja_output(result)

    # Update session state
    if raja_output.detected_mood:
        session.current_mood = raja_output.detected_mood
    if raja_output.recommended_drink_id:
        session.last_recommended_drink = raja_output.recommended_drink_id
    session.mentioned_drinks.extend(raja_output.drinks_mentioned)
    session.mentioned_ingredients.extend(raja_output.ingredients_mentioned)

    # Add Raja's response to history
    raja_message = ChatMessage(
        id=str(uuid.uuid4()),
        role=MessageRole.RAJA,
        content=raja_output.response,
        intent=raja_output.detected_intent,
        metadata={
            "drinks_mentioned": raja_output.drinks_mentioned,
            "recommendation_made": raja_output.recommendation_made,
        },
    )
    session.history.add_message(raja_message)

    # Build drink references with names
    drink_refs = []
    for drink_id in raja_output.drinks_mentioned:
        drink_data = _get_drink_by_id(drink_id)
        if drink_data:
            drink_refs.append(
                DrinkReference(
                    id=drink_id,
                    name=drink_data.get("name", drink_id.replace("-", " ").title()),
                    mentioned_reason="",
                )
            )

    total_elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"run_raja_chat completed in {total_elapsed_ms:.2f}ms: "
        f"intent={raja_output.detected_intent}, recommendation={raja_output.recommendation_made}"
    )

    return ChatResponse(
        session_id=session.session_id,
        message_id=raja_message.id,
        content=raja_output.response,
        drinks_mentioned=drink_refs,
        ingredients_mentioned=raja_output.ingredients_mentioned,
        suggested_action=_get_suggested_action(raja_output),
        recommendation_offered=raja_output.recommendation_made,
        recommended_drink_id=raja_output.recommended_drink_id,
        special_recipe=raja_output.special_recipe,
    )


def get_session(session_id: str) -> ChatSession | None:
    """Get a chat session by ID.

    Args:
        session_id: The session ID to retrieve.

    Returns:
        ChatSession if found, None otherwise.
    """
    return _chat_sessions.get(session_id)


def delete_session(session_id: str) -> bool:
    """Delete a chat session.

    Args:
        session_id: The session ID to delete.

    Returns:
        True if deleted, False if not found.
    """
    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
        logger.info(f"Deleted chat session: {session_id}")
        return True
    return False
