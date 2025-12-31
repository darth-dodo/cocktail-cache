"""Pydantic models for Raja conversational chat interface.

These models provide structured data for chat messages, history management,
and integration with the existing recommendation flow.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message participant."""

    USER = "user"
    RAJA = "raja"
    SYSTEM = "system"


class MessageIntent(str, Enum):
    """Detected intent of a user message for routing decisions."""

    GREETING = "greeting"
    RECOMMENDATION_REQUEST = "recommendation_request"
    RECIPE_QUESTION = "recipe_question"
    TECHNIQUE_QUESTION = "technique_question"
    INGREDIENT_QUESTION = "ingredient_question"
    GENERAL_CHAT = "general_chat"
    CABINET_UPDATE = "cabinet_update"
    FEEDBACK = "feedback"
    GOODBYE = "goodbye"


class ChatMessage(BaseModel):
    """A single message in the chat conversation."""

    id: str = Field(..., description="Unique message identifier (UUID)")
    role: MessageRole = Field(..., description="Who sent this message")
    content: str = Field(..., description="Message text content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the message was sent"
    )
    intent: MessageIntent | None = Field(
        default=None, description="Detected intent (only for user messages)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (e.g., referenced drink, ingredient)",
    )


class ChatHistory(BaseModel):
    """Collection of messages forming the conversation history."""

    messages: list[ChatMessage] = Field(
        default_factory=list, description="Ordered list of messages, oldest first"
    )
    max_messages: int = Field(
        default=50, description="Maximum messages to retain in history"
    )

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to history, trimming if over limit."""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            # Keep system messages and recent conversation
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            recent_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM][
                -self.max_messages + len(system_msgs) :
            ]
            self.messages = system_msgs + recent_msgs

    def get_context_window(self, last_n: int = 10) -> list[ChatMessage]:
        """Get the last N messages for context injection."""
        return self.messages[-last_n:]

    def format_for_prompt(self, last_n: int = 10) -> str:
        """Format recent history for injection into agent prompt."""
        context = self.get_context_window(last_n)
        if not context:
            return "No previous conversation."

        lines = []
        for msg in context:
            role_label = "Customer" if msg.role == MessageRole.USER else "Raja"
            lines.append(f"{role_label}: {msg.content}")
        return "\n".join(lines)


class ChatSession(BaseModel):
    """A chat session with Raja, including user context."""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    history: ChatHistory = Field(default_factory=ChatHistory)

    # User context carried through conversation
    cabinet: list[str] = Field(
        default_factory=list, description="User's available ingredients"
    )
    skill_level: str = Field(
        default="intermediate", description="User's bartending skill level"
    )
    drink_type_preference: str = Field(
        default="cocktail", description="Preferred drink type"
    )
    current_mood: str | None = Field(
        default=None, description="Current mood extracted from conversation"
    )

    # Conversation state
    last_recommended_drink: str | None = Field(
        default=None, description="ID of the last drink Raja recommended"
    )
    mentioned_drinks: list[str] = Field(
        default_factory=list, description="Drinks mentioned in conversation"
    )
    mentioned_ingredients: list[str] = Field(
        default_factory=list, description="Ingredients mentioned in conversation"
    )


class ChatRequest(BaseModel):
    """Request model for sending a message to Raja."""

    session_id: str | None = Field(
        default=None, description="Existing session ID, or None to start new session"
    )
    message: str = Field(
        ..., min_length=1, max_length=2000, description="User's message to Raja"
    )
    cabinet: list[str] | None = Field(
        default=None,
        description="User's cabinet (only needed on first message or update)",
    )
    skill_level: str | None = Field(
        default=None, description="Skill level (only needed on first message or update)"
    )
    drink_type: str | None = Field(
        default=None,
        description="Drink preference (only needed on first message or update)",
    )


class DrinkReference(BaseModel):
    """A drink referenced in Raja's response."""

    id: str = Field(..., description="Drink identifier")
    name: str = Field(..., description="Display name")
    mentioned_reason: str = Field(
        default="", description="Why Raja mentioned this drink"
    )


class SpecialRecipe(BaseModel):
    """A recipe for a drink not in our database - Raja's special from memory."""

    name: str = Field(..., description="Name of the drink")
    tagline: str = Field(default="", description="Short description of the drink")
    ingredients: list[str] = Field(
        ..., description="List of ingredients with amounts (e.g., '30 ml bourbon')"
    )
    method: list[str] = Field(..., description="Step-by-step preparation instructions")
    glassware: str = Field(default="", description="Recommended glass type")
    garnish: str = Field(default="", description="Garnish suggestion")
    tip: str = Field(default="", description="Raja's personal tip for this drink")


class ChatResponse(BaseModel):
    """Response from Raja in the chat."""

    session_id: str = Field(..., description="Session ID for follow-up")
    message_id: str = Field(..., description="ID of Raja's response message")
    content: str = Field(..., description="Raja's response text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Extracted entities for UI enhancement
    drinks_mentioned: list[DrinkReference] = Field(
        default_factory=list, description="Drinks Raja mentioned (clickable in UI)"
    )
    ingredients_mentioned: list[str] = Field(
        default_factory=list, description="Ingredients Raja mentioned"
    )
    suggested_action: str | None = Field(
        default=None,
        description="Suggested next action (e.g., 'view_recipe', 'update_cabinet')",
    )

    # For recommendation integration
    recommendation_offered: bool = Field(
        default=False, description="Whether Raja offered a specific recommendation"
    )
    recommended_drink_id: str | None = Field(
        default=None, description="ID of recommended drink if any"
    )

    # For special recipes not in our database
    special_recipe: SpecialRecipe | None = Field(
        default=None,
        description="Full recipe for a drink NOT in our database - Raja's special",
    )


class RajaChatOutput(BaseModel):
    """Structured output from the Raja chat agent task."""

    response: str = Field(..., description="Raja's conversational response")
    detected_intent: MessageIntent = Field(
        default=MessageIntent.GENERAL_CHAT, description="What the user is asking for"
    )
    detected_mood: str | None = Field(
        default=None, description="Mood extracted from conversation"
    )
    drinks_mentioned: list[str] = Field(
        default_factory=list, description="Drink IDs mentioned in response"
    )
    ingredients_mentioned: list[str] = Field(
        default_factory=list, description="Ingredient IDs mentioned in response"
    )
    recommendation_made: bool = Field(
        default=False, description="Whether a specific drink was recommended"
    )
    recommended_drink_id: str | None = Field(
        default=None, description="ID of recommended drink if any"
    )
    suggested_follow_up: str | None = Field(
        default=None, description="Suggested topic for continuing conversation"
    )
    special_recipe: SpecialRecipe | None = Field(
        default=None,
        description="Full recipe for a drink NOT in our database - Raja's special from memory",
    )
