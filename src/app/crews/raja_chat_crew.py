"""Raja Chat Crew for conversational cocktail interactions.

This crew provides a personality-rich chat experience with Raja,
a bartender from Bombay who offers cocktail advice through natural
conversation.

The crew maintains conversation context and integrates with the
existing drink data services for accurate recommendations.
"""

import logging
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
from src.app.tools import RecipeDBTool
from src.app.utils.parsing import parse_json_from_llm_output

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


def create_raja_chat_crew(session: ChatSession, user_message: str) -> Crew:
    """Create the Raja Chat Crew for conversational interactions.

    The crew uses a single Raja Bartender agent that:
    - Receives conversation history and user context
    - Uses RecipeDBTool to dynamically look up drinks

    Args:
        session: The chat session with history and user context.
        user_message: The user's current message.

    Returns:
        A configured CrewAI Crew instance.
    """
    logger.info(f"Creating Raja chat crew for session {session.session_id}")

    # Create Raja agent with RecipeDBTool for dynamic drink lookup
    recipe_tool = RecipeDBTool()
    raja = create_raja_bartender(tools=[recipe_tool])

    # Format conversation history
    history_text = session.history.format_for_prompt(last_n=8)

    # Format cabinet for display
    cabinet_text = "No cabinet set up yet."
    if session.cabinet:
        cabinet_text = f"{len(session.cabinet)} bottles: {', '.join(session.cabinet[:20])}{'...' if len(session.cabinet) > 20 else ''}"

    # Build the chat task with simplified context
    chat_task = Task(
        description=f"""You are Raja, responding to a customer in your bar. Stay in character!

CONVERSATION SO FAR:
{history_text}

CUSTOMER'S LATEST MESSAGE:
{user_message}

CUSTOMER'S BAR CABINET:
{cabinet_text}

CUSTOMER INFO:
- Skill Level: {session.skill_level}
- Drink Preference: {session.drink_type_preference}
- Current Mood: {session.current_mood or "not yet determined"}

TOOL USAGE:
When recommending drinks, USE the recipe_database tool to search for drinks the customer can make.
- Pass their cabinet ingredients and drink_type preference to find matching drinks
- The tool returns drinks with match scores (1.0 = all ingredients available)
- Only recommend drinks that appear in the tool results with their EXACT IDs

INSTRUCTIONS:
1. BE SNAPPY! 2-3 sentences max. Get to the point with warmth. No long monologues.
2. Use respectful Hindi: "yaar", "bhai", "acha", "bilkul", "of course", "kya baat hai". Keep it friendly.
3. For recommendations: Use the recipe_database tool first, then make your pick based on the customer's mood and preferences.
4. CRITICAL: Only share SECOND-HAND stories. Say "I heard...", "They say...", "Legend has it...", "An old regular once told me...". NEVER first-person experiences like "I remember when I..." or "Back when I served...".
5. Be encouraging but concise. Warm and wise, not lengthy lectures.
6. If they need ingredients, tell them kindly - "Yaar, grab some X and you're all set."

CRITICAL - DRINK RECOMMENDATIONS:
- ALWAYS use the recipe_database tool to find drinks before recommending.
- ONLY use "recommended_drink_id" if the drink appears in tool results with that exact ID.
- If recommending a drink NOT in tool results, use "special_recipe" instead.
  This is "Raja's Special from Memory" - a drink you know but we don't have in our collection.
  Include: name, tagline, ingredients (with amounts like "20 ml bourbon"), method (step-by-step), glassware, garnish, and your personal tip.
- NEVER invent or guess drink IDs. If unsure, use special_recipe.

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

TOOL USAGE: For recommendations, call recipe_database tool with:
- cabinet: list of customer's ingredients
- drink_type: "cocktails", "mocktails", or "both"
The tool returns drinks with match scores. Use IDs from results for recommended_drink_id.

If drink is NOT in tool results, include special_recipe:
{{
  "response": "Arrey yaar, let me share a special one from my memory...",
  "recommendation_made": true,
  "recommended_drink_id": null,
  "special_recipe": {{
    "name": "Drink Name",
    "tagline": "Short description",
    "ingredients": ["60 ml bourbon", "30 ml sweet vermouth", "2 dashes bitters"],
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

    parsed = parse_json_from_llm_output(
        raw_output, RajaChatOutput, logger, "Raja output"
    )
    if parsed:
        return parsed

    # Final fallback
    return RajaChatOutput(
        response=raw_output
        if raw_output
        else "Arrey, something went wrong! Can you please try again, yaar.",
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

    result = crew.kickoff()

    # Parse output
    raja_output = _parse_raja_output(result)

    # Validate recommended_drink_id against our database
    # If Raja recommends a drink not in our DB, clear the ID to prevent dead links
    if raja_output.recommended_drink_id:
        all_drink_ids = {drink.id for drink in load_all_drinks()}
        if raja_output.recommended_drink_id not in all_drink_ids:
            logger.warning(
                f"Raja recommended unknown drink: {raja_output.recommended_drink_id}, clearing ID"
            )
            raja_output.recommended_drink_id = None
            # Note: If special_recipe was also provided by Raja, it will still be used

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
