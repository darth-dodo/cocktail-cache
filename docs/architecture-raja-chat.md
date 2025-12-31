# Architecture: Raja Conversational Chat Interface

> **Last Updated**: December 2025 (Tool-Based Architecture)
> **Status**: Implemented
> **Tests**: 761 passing

## Executive Summary

This document outlines the architecture for the conversational chat interface featuring Raja, a bartender from Bombay, as an AI-powered cocktail advisor. The design integrates with CrewAI patterns using a **tool-based architecture** where Raja dynamically accesses drink data through 4 specialized tools rather than static prompt injection.

---

## 1. System Architecture Overview

```
+-------------------+     +-------------------+     +-------------------+
|   Frontend Chat   |     |   FastAPI Chat    |     |    Raja Chat     |
|     Component     | --> |     Endpoint      | --> |      Crew        |
+-------------------+     +-------------------+     +-------------------+
         |                        |                         |
         |                        v                         v
         |                +----------------+        +------------------+
         |                | Chat Session   |        | Raja Bartender   |
         |                |   Manager      |        |  Agent + Tools   |
         |                +----------------+        +------------------+
         |                        |                         |
         v                        v                         v
+-------------------+     +-------------------+     +-------------------+
|  Chat History     |     |   Memory Store    |     |  4 Cocktail      |
|    Display        |     |   (dict)          |     |    Tools         |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                    +-------+-------+
                                                    |               |
                                              +----------+    +----------+
                                              | Recipe   |    | Substit- |
                                              | DBTool   |    | ution    |
                                              +----------+    +----------+
                                                    |               |
                                              +----------+    +----------+
                                              | Unlock   |    | Flavor   |
                                              | Calc     |    | Profiler |
                                              +----------+    +----------+
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| Frontend Chat | Message input, history display, typing indicators |
| FastAPI Endpoint | Request validation, session management, response handling |
| Chat Session Manager | History persistence, context window management, session lifecycle |
| Raja Chat Crew | Orchestrates Raja agent with minimal context + tool access |
| Raja Bartender Agent | Personality-consistent responses with dynamic tool usage |
| 4 Cocktail Tools | Dynamic data access: recipes, substitutions, unlocks, flavors |

---

## 2. Agent Configuration

### New Agent: `raja_bartender`

Add to `/Users/abhishek/stuff/ai-adventures/cocktail-cache/src/app/agents/config/agents.yaml`:

```yaml
raja_bartender:
  role: "Raja - Your Bombay Bartender"
  goal: "Have natural, personality-rich conversations about cocktails while providing expert mixology advice"
  backstory: >
    You are Raja, a charismatic bartender from Colaba, Bombay (now Mumbai). You've been
    behind the bar for 20 years, starting at Leopold Cafe and now running your own
    speakeasy. You speak with warmth and occasional Hindi phrases ("Arrey bhai!",
    "Ekdum first class!", "Kya baat hai!"). You have strong opinions about cocktails -
    you believe a good drink tells a story. You love sharing the history behind drinks
    and often relate them to your experiences in Bombay's bar scene. You're patient
    with beginners but can go deep with enthusiasts. You occasionally reference Bollywood,
    cricket, and monsoon season when describing drinks. When someone asks for a
    recommendation, you ask about their mood, what they had for dinner, or what music
    they're listening to - because context matters for the perfect drink.
  verbose: false
  allow_delegation: false
```

### New LLM Configuration for Conversational Use

Add to `/Users/abhishek/stuff/ai-adventures/cocktail-cache/src/app/agents/config/llm.yaml`:

```yaml
conversational:
  model: "anthropic/claude-3-5-haiku-20241022"
  max_tokens: 1024
  temperature: 0.85  # Higher for more personality variation
```

---

## 3. Pydantic Models for Chat I/O

Create new file: `/Users/abhishek/stuff/ai-adventures/cocktail-cache/src/app/models/chat.py`

```python
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
        default_factory=datetime.utcnow,
        description="When the message was sent"
    )
    intent: MessageIntent | None = Field(
        default=None,
        description="Detected intent (only for user messages)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (e.g., referenced drink, ingredient)"
    )


class ChatHistory(BaseModel):
    """Collection of messages forming the conversation history."""

    messages: list[ChatMessage] = Field(
        default_factory=list,
        description="Ordered list of messages, oldest first"
    )
    max_messages: int = Field(
        default=50,
        description="Maximum messages to retain in history"
    )

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to history, trimming if over limit."""
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            # Keep system messages and recent conversation
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            recent_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM][-self.max_messages + len(system_msgs):]
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
        default_factory=list,
        description="User's available ingredients"
    )
    skill_level: str = Field(
        default="intermediate",
        description="User's bartending skill level"
    )
    drink_type_preference: str = Field(
        default="cocktail",
        description="Preferred drink type"
    )
    current_mood: str | None = Field(
        default=None,
        description="Current mood extracted from conversation"
    )

    # Conversation state
    last_recommended_drink: str | None = Field(
        default=None,
        description="ID of the last drink Raja recommended"
    )
    mentioned_drinks: list[str] = Field(
        default_factory=list,
        description="Drinks mentioned in conversation"
    )
    mentioned_ingredients: list[str] = Field(
        default_factory=list,
        description="Ingredients mentioned in conversation"
    )


class ChatRequest(BaseModel):
    """Request model for sending a message to Raja."""

    session_id: str | None = Field(
        default=None,
        description="Existing session ID, or None to start new session"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message to Raja"
    )
    cabinet: list[str] | None = Field(
        default=None,
        description="User's cabinet (only needed on first message or update)"
    )
    skill_level: str | None = Field(
        default=None,
        description="Skill level (only needed on first message or update)"
    )
    drink_type: str | None = Field(
        default=None,
        description="Drink preference (only needed on first message or update)"
    )


class DrinkReference(BaseModel):
    """A drink referenced in Raja's response."""

    id: str = Field(..., description="Drink identifier")
    name: str = Field(..., description="Display name")
    mentioned_reason: str = Field(
        default="",
        description="Why Raja mentioned this drink"
    )


class ChatResponse(BaseModel):
    """Response from Raja in the chat."""

    session_id: str = Field(..., description="Session ID for follow-up")
    message_id: str = Field(..., description="ID of Raja's response message")
    content: str = Field(..., description="Raja's response text")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Extracted entities for UI enhancement
    drinks_mentioned: list[DrinkReference] = Field(
        default_factory=list,
        description="Drinks Raja mentioned (clickable in UI)"
    )
    ingredients_mentioned: list[str] = Field(
        default_factory=list,
        description="Ingredients Raja mentioned"
    )
    suggested_action: str | None = Field(
        default=None,
        description="Suggested next action (e.g., 'view_recipe', 'update_cabinet')"
    )

    # For recommendation integration
    recommendation_offered: bool = Field(
        default=False,
        description="Whether Raja offered a specific recommendation"
    )
    recommended_drink_id: str | None = Field(
        default=None,
        description="ID of recommended drink if any"
    )


class RajaChatOutput(BaseModel):
    """Structured output from the Raja chat agent task."""

    response: str = Field(
        ...,
        description="Raja's conversational response"
    )
    detected_intent: MessageIntent = Field(
        default=MessageIntent.GENERAL_CHAT,
        description="What the user is asking for"
    )
    detected_mood: str | None = Field(
        default=None,
        description="Mood extracted from conversation"
    )
    drinks_mentioned: list[str] = Field(
        default_factory=list,
        description="Drink IDs mentioned in response"
    )
    ingredients_mentioned: list[str] = Field(
        default_factory=list,
        description="Ingredient IDs mentioned in response"
    )
    recommendation_made: bool = Field(
        default=False,
        description="Whether a specific drink was recommended"
    )
    recommended_drink_id: str | None = Field(
        default=None,
        description="ID of recommended drink if any"
    )
    suggested_follow_up: str | None = Field(
        default=None,
        description="Suggested topic for continuing conversation"
    )
```

---

## 4. Raja Chat Crew Implementation (Tool-Based)

The current implementation uses a **tool-based architecture** where Raja dynamically queries drink data through CrewAI tools.

**File**: `src/app/crews/raja_chat_crew.py`

### Key Architecture Change: Tools vs Data Injection

```
BEFORE (Data Injection - DEPRECATED):
┌─────────────────────────────────────────────────────┐
│ User Message                                        │
│ + Full Drink Database (injected ~4000 tokens)      │
│ + Cabinet Contents (injected)                       │
│ + Substitutions (injected)                          │
└─────────────────────┬───────────────────────────────┘
                      ▼
              ┌───────────────┐
              │  Raja Agent   │
              │  (no tools)   │
              └───────────────┘

AFTER (Tool-Based - CURRENT):
┌─────────────────────────────────────────────────────┐
│ User Message + Cabinet Context (minimal ~1000 tokens)│
└─────────────────────┬───────────────────────────────┘
                      ▼
              ┌───────────────┐
              │  Raja Agent   │◄────┐
              │ (with 4 tools)│     │
              └───────┬───────┘     │
                      │             │
        ┌─────────────┼─────────────┼─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
   │ Recipe  │  │ Substi-  │  │ Unlock   │  │ Flavor  │
   │ DBTool  │  │ tution   │  │ Calc     │  │ Profiler│
   └─────────┘  └──────────┘  └──────────┘  └─────────┘
```

### Benefits of Tool-Based Architecture
- **Smaller prompts**: ~1000 tokens vs ~4000 tokens per message
- **Dynamic data**: Raja queries only what's needed for the conversation
- **More natural UX**: "Let me check what you can make..." feels authentic
- **Accurate recommendations**: Uses actual database IDs, validated post-response

### Current Implementation

```python
def create_raja_chat_crew(session: ChatSession, user_message: str) -> Crew:
    """Create the Raja Chat Crew with tool access."""

    # Create Raja with RecipeDBTool for dynamic drink lookup
    # Raja also has 3 default tools: substitution_finder, unlock_calculator, flavor_profiler
    recipe_tool = RecipeDBTool()
    raja = create_raja_bartender(tools=[recipe_tool])  # Gets 4 tools total

    # Minimal context - just cabinet summary, not full drink list
    cabinet_text = f"{len(session.cabinet)} bottles: {', '.join(session.cabinet[:20])}"

    chat_task = Task(
        description=f"""You are Raja, responding to a customer in your bar.

CUSTOMER'S BAR CABINET: {cabinet_text}
CUSTOMER INFO: Skill={session.skill_level}, Preference={session.drink_type_preference}

TOOL USAGE:
When recommending drinks, USE the recipe_database tool to search for drinks.
- Pass cabinet ingredients and drink_type preference
- Tool returns drinks with match scores (1.0 = all ingredients available)
- Only recommend drinks from tool results with EXACT IDs

INSTRUCTIONS:
1. BE SNAPPY! 2-3 sentences max.
2. Use respectful Hindi: "yaar", "bhai", "bilkul"
3. For recommendations: Use recipe_database tool first
4. CRITICAL: Only SECOND-HAND stories ("I heard...", "Legend has it...")
5. If drink NOT in tool results, use special_recipe field instead
""",
        agent=raja,
        output_pydantic=RajaChatOutput,
    )

    return Crew(agents=[raja], tasks=[chat_task], process=Process.sequential)
```

### Drink ID Validation

The system validates recommended drink IDs against the database:

```python
def run_raja_chat(request: ChatRequest) -> ChatResponse:
    # ... run crew ...
    raja_output = _parse_raja_output(result)

    # Validate recommended_drink_id against database
    if raja_output.recommended_drink_id:
        all_drink_ids = {drink.id for drink in load_all_drinks()}
        if raja_output.recommended_drink_id not in all_drink_ids:
            logger.warning(f"Raja recommended unknown drink: {raja_output.recommended_drink_id}")
            raja_output.recommended_drink_id = None  # Clear invalid ID

    return ChatResponse(...)
```

### Special Recipe Fallback

When Raja recommends a drink not in the database, the special_recipe field provides a complete recipe:

```python
class RajaChatOutput(BaseModel):
    response: str
    recommended_drink_id: str | None = None  # Only if in database
    special_recipe: SpecialRecipe | None = None  # For "Raja's memory" drinks

class SpecialRecipe(BaseModel):
    name: str
    tagline: str
    ingredients: list[str]  # With amounts: "60 ml bourbon"
    method: list[str]
    glassware: str
    garnish: str
    tip: str  # Raja's personal tip
```

---

## 5. Raja Bartender Agent Factory (with Default Tools)

**File**: `src/app/agents/raja_bartender.py`

The agent factory now includes 4 default tools for dynamic data access:

```python
"""Raja Bartender agent with integrated cocktail tools."""

from crewai import LLM, Agent

from src.app.agents.config import get_agent_config
from src.app.agents.llm_config import get_llm
from src.app.tools import (
    FlavorProfilerTool,
    RecipeDBTool,
    SubstitutionFinderTool,
    UnlockCalculatorTool,
)

# Default tools Raja uses for dynamic data access
DEFAULT_RAJA_TOOLS = [
    RecipeDBTool(),           # Search drinks by ingredients
    SubstitutionFinderTool(), # Find ingredient alternatives
    UnlockCalculatorTool(),   # Calculate best bottles to buy
    FlavorProfilerTool(),     # Analyze/compare drink flavors
]


def create_raja_bartender(
    tools: list | None = None,
    llm: LLM | None = None,
    include_default_tools: bool = True,
) -> Agent:
    """Create Raja Bartender with cocktail tools.

    Args:
        tools: Additional tools beyond defaults.
        llm: Custom LLM (defaults to conversational profile).
        include_default_tools: Include 4 cocktail tools (default True).

    Returns:
        Configured Raja Agent with tools.
    """
    config = get_agent_config("raja_bartender")

    # Combine default tools with any custom tools
    all_tools = []
    if include_default_tools:
        all_tools.extend(DEFAULT_RAJA_TOOLS)
    if tools:
        all_tools.extend(tools)

    return Agent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        tools=all_tools,
        llm=llm or get_llm("conversational"),
        verbose=config.verbose,
        allow_delegation=config.allow_delegation,
    )
```

### Tool Descriptions (Raja-Optimized)

Each tool has descriptions optimized for Raja's conversational style:

| Tool | Description for Agent |
|------|----------------------|
| `recipe_database` | "Search Raja's drink database. Returns drinks with match scores." |
| `substitution_finder` | "Find alternative ingredients. Arrey, no bourbon? Let me check!" |
| `unlock_calculator` | "Calculate ROI for new bottles. Which purchase unlocks most drinks?" |
| `flavor_profiler` | "Analyze drink flavor profiles for comparison recommendations." |

---

## 6. API Endpoint Design

Add to `/Users/abhishek/stuff/ai-adventures/cocktail-cache/src/app/routers/api.py`:

```python
# =============================================================================
# Raja Chat Endpoints
# =============================================================================

from src.app.models.chat import ChatRequest, ChatResponse, ChatSession
from src.app.crews.raja_chat_crew import get_or_create_session, run_raja_chat


class ChatHistoryResponse(BaseModel):
    """Response with chat history for session restore."""

    session_id: str
    messages: list[dict[str, Any]]
    cabinet: list[str]
    skill_level: str
    current_mood: str | None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_raja(request: ChatRequest) -> ChatResponse:
    """Send a message to Raja and get his response.

    Start a new conversation by omitting session_id, or continue
    an existing one by providing the session_id from a previous response.

    Cabinet, skill_level, and drink_type only need to be provided on
    the first message or when updating context.

    Args:
        request: Chat request with message and optional context.

    Returns:
        ChatResponse with Raja's message and metadata.

    Example:
        # Start new conversation
        POST /api/chat
        {
            "message": "Hey Raja, what should I drink tonight?",
            "cabinet": ["bourbon", "sweet-vermouth", "angostura-bitters"],
            "skill_level": "intermediate"
        }

        # Continue conversation
        POST /api/chat
        {
            "session_id": "abc123-def456",
            "message": "Something strong but not too sweet"
        }
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    logger.info(f"Chat request: session={request.session_id}, message_len={len(request.message)}")

    # Run the synchronous crew in a thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        response = await loop.run_in_executor(
            executor,
            run_raja_chat,
            request,
        )

    return response


@router.get("/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str) -> ChatHistoryResponse:
    """Get chat history for a session.

    Useful for restoring a conversation after page refresh or
    displaying conversation history in the UI.

    Args:
        session_id: The session ID to retrieve history for.

    Returns:
        ChatHistoryResponse with messages and session context.

    Raises:
        HTTPException: If session not found.
    """
    from src.app.crews.raja_chat_crew import _chat_sessions

    session = _chat_sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session not found: {session_id}",
        )

    return ChatHistoryResponse(
        session_id=session.session_id,
        messages=[
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in session.history.messages
        ],
        cabinet=session.cabinet,
        skill_level=session.skill_level,
        current_mood=session.current_mood,
    )


@router.delete("/chat/{session_id}")
async def end_chat_session(session_id: str) -> dict[str, str]:
    """End a chat session and clean up resources.

    Args:
        session_id: The session ID to end.

    Returns:
        Confirmation message.
    """
    from src.app.crews.raja_chat_crew import _chat_sessions

    if session_id in _chat_sessions:
        del _chat_sessions[session_id]
        logger.info(f"Ended chat session: {session_id}")
        return {"message": f"Session {session_id} ended. See you next time!"}

    return {"message": "Session not found or already ended."}
```

---

## 7. Frontend Integration Approach

### New Template: `/Users/abhishek/stuff/ai-adventures/cocktail-cache/src/app/templates/chat.html`

The chat interface should include:

```html
{% extends "base.html" %}

{% block content %}
<div id="chat-container" class="flex flex-col h-[calc(100vh-4rem)]">
    <!-- Chat Header -->
    <div class="flex items-center gap-3 p-4 border-b border-amber-200 bg-amber-50">
        <div class="w-12 h-12 rounded-full bg-amber-600 flex items-center justify-center">
            <span class="text-2xl">🍸</span>
        </div>
        <div>
            <h1 class="font-bold text-lg text-amber-900">Raja</h1>
            <p class="text-sm text-amber-700">Your Bombay Bartender</p>
        </div>
    </div>

    <!-- Messages Area -->
    <div id="messages" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Messages rendered here -->
    </div>

    <!-- Typing Indicator -->
    <div id="typing-indicator" class="hidden px-4 py-2">
        <div class="flex items-center gap-2 text-amber-600">
            <span class="animate-pulse">Raja is mixing up a response...</span>
        </div>
    </div>

    <!-- Input Area -->
    <div class="p-4 border-t border-amber-200 bg-white">
        <form id="chat-form" class="flex gap-2">
            <input
                type="text"
                id="message-input"
                placeholder="Ask Raja about cocktails..."
                class="flex-1 px-4 py-2 border border-amber-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                autocomplete="off"
            />
            <button
                type="submit"
                class="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
            >
                Send
            </button>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', path='js/raja-chat.js') }}"></script>
{% endblock %}
```

### New JavaScript: `/Users/abhishek/stuff/ai-adventures/cocktail-cache/src/app/static/js/raja-chat.js`

```javascript
/**
 * Raja Chat Interface
 * Handles conversation with Raja the bartender
 */

class RajaChat {
    constructor() {
        this.sessionId = null;
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('message-input');
        this.chatForm = document.getElementById('chat-form');
        this.typingIndicator = document.getElementById('typing-indicator');

        this.init();
    }

    init() {
        // Check for existing session in localStorage
        this.sessionId = localStorage.getItem('raja_session_id');

        if (this.sessionId) {
            this.loadHistory();
        }

        // Set up event listeners
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Get cabinet from shared state
        this.cabinet = window.cabinetState?.getSelected() || [];
    }

    async loadHistory() {
        try {
            const response = await fetch(`/api/chat/${this.sessionId}/history`);
            if (response.ok) {
                const data = await response.json();
                data.messages.forEach(msg => this.renderMessage(msg));
            } else {
                // Session expired, start fresh
                this.sessionId = null;
                localStorage.removeItem('raja_session_id');
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    async handleSubmit(event) {
        event.preventDefault();

        const message = this.messageInput.value.trim();
        if (!message) return;

        // Clear input
        this.messageInput.value = '';

        // Render user message immediately
        this.renderMessage({
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
        });

        // Show typing indicator
        this.showTyping();

        try {
            const requestBody = {
                message: message,
            };

            // Include session_id if we have one
            if (this.sessionId) {
                requestBody.session_id = this.sessionId;
            } else {
                // First message - include cabinet and preferences
                requestBody.cabinet = window.cabinetState?.getSelected() || [];
                requestBody.skill_level = localStorage.getItem('skill_level') || 'intermediate';
                requestBody.drink_type = localStorage.getItem('drink_type') || 'cocktail';
            }

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                throw new Error('Chat request failed');
            }

            const data = await response.json();

            // Store session ID
            this.sessionId = data.session_id;
            localStorage.setItem('raja_session_id', this.sessionId);

            // Render Raja's response
            this.renderMessage({
                role: 'raja',
                content: data.content,
                timestamp: data.timestamp,
                drinks_mentioned: data.drinks_mentioned,
                suggested_action: data.suggested_action,
            });

        } catch (error) {
            console.error('Chat error:', error);
            this.renderMessage({
                role: 'raja',
                content: 'Arrey, something went wrong on my end! Try again, yaar.',
                timestamp: new Date().toISOString(),
            });
        } finally {
            this.hideTyping();
        }
    }

    renderMessage(message) {
        const isRaja = message.role === 'raja';

        const messageEl = document.createElement('div');
        messageEl.className = `flex ${isRaja ? 'justify-start' : 'justify-end'}`;

        const bubbleEl = document.createElement('div');
        bubbleEl.className = `max-w-[80%] px-4 py-3 rounded-2xl ${
            isRaja
                ? 'bg-amber-100 text-amber-900 rounded-bl-none'
                : 'bg-blue-600 text-white rounded-br-none'
        }`;

        // Parse content for drink mentions (clickable links)
        let content = message.content;
        if (message.drinks_mentioned?.length > 0) {
            message.drinks_mentioned.forEach(drink => {
                const linkHtml = `<a href="/drink/${drink.id}" class="underline font-semibold hover:text-amber-700">${drink.name}</a>`;
                // Simple replacement - could be improved with regex
                content = content.replace(new RegExp(drink.name, 'gi'), linkHtml);
            });
        }

        bubbleEl.innerHTML = content;
        messageEl.appendChild(bubbleEl);

        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    showTyping() {
        this.typingIndicator.classList.remove('hidden');
        this.scrollToBottom();
    }

    hideTyping() {
        this.typingIndicator.classList.add('hidden');
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.rajaChat = new RajaChat();
});
```

---

## 8. File Structure Summary

```
src/app/
├── agents/
│   ├── config/
│   │   ├── agents.yaml          # Add raja_bartender config
│   │   └── llm.yaml             # Add conversational profile
│   ├── __init__.py              # Export create_raja_bartender
│   └── raja_bartender.py        # NEW: Raja agent factory
├── crews/
│   ├── __init__.py              # Export raja_chat_crew functions
│   └── raja_chat_crew.py        # NEW: Raja chat crew
├── models/
│   ├── __init__.py              # Export chat models
│   └── chat.py                  # NEW: Chat Pydantic models
├── routers/
│   └── api.py                   # Add /chat endpoints
├── templates/
│   └── chat.html                # NEW: Chat interface template
├── static/
│   └── js/
│       └── raja-chat.js         # NEW: Chat frontend logic
└── main.py                      # Add /chat route
```

---

## 9. Key Design Decisions

### 9.1 Tool-Based vs Data Injection Architecture

**Decision**: Use CrewAI tools for dynamic data access instead of prompt injection.

**Rationale**:
- **Token efficiency**: ~1000 tokens vs ~4000 tokens per message
- **Dynamic data**: Raja queries only what's needed, when needed
- **Natural UX**: "Let me check..." feels authentic for a bartender
- **Accuracy**: Tool results provide exact drink IDs, validated post-response

**Trade-offs**:
- ⚠️ More LLM calls (tool use adds round-trips)
- ⚠️ Slightly slower responses (tool execution time)
- ✅ Smaller context = lower cost per message
- ✅ More accurate recommendations

### 9.2 Four Default Tools for Raja

**Decision**: Raja has 4 default tools: RecipeDBTool, SubstitutionFinderTool, UnlockCalculatorTool, FlavorProfilerTool.

**Rationale**:
- Cover all common conversation intents (recommendations, substitutions, bar growth, flavor comparisons)
- Tools have Raja-friendly descriptions for natural usage
- `include_default_tools=False` option for testing or custom setups

### 9.3 Drink ID Validation

**Decision**: Validate `recommended_drink_id` against database after parsing.

**Rationale**:
- LLM may hallucinate drink IDs not in database
- Invalid IDs would create dead links in UI
- Validation clears invalid IDs, allowing fallback to `special_recipe`

### 9.4 Special Recipe Fallback

**Decision**: When Raja recommends a drink not in the database, use `special_recipe` field.

**Rationale**:
- Raja can share drinks from "memory" not in our 142-drink collection
- Provides complete recipe with amounts, method, glassware
- Maintains conversation flow without errors

### 9.5 Chat History Management

**Decision**: Server-side session storage with configurable context window.

**Rationale**:
- Maintains conversation continuity across messages
- Limits context injection to last N messages (default 8) to manage token usage
- Session cleanup after inactivity prevents memory bloat

### 9.6 Personality Persistence

**Decision**: Backstory and personality traits defined in YAML config.

**Rationale**:
- Easy to tune Raja's personality without code changes
- Consistent with existing agent configuration patterns
- Hindi phrases and cultural references in backstory guide LLM behavior
- Higher temperature (0.85) allows natural variation in personality expression

---

## 10. Future Enhancements

### 10.1 Streaming Responses
- Implement SSE or WebSocket for real-time typing effect
- Show Raja's response as it generates

### 10.2 Voice Interface
- Add speech-to-text for message input
- Text-to-speech for Raja's responses (with Bombay accent!)

### 10.3 Proactive Suggestions
- Raja can notice patterns ("You've been asking about bourbon drinks - have you tried an Old Fashioned?")
- Time-based suggestions ("It's evening - time for something spirit-forward, no?")

### 10.4 Multi-Language Support
- Detect user's language preference
- Raja can respond in Hindi, Marathi, or other Indian languages

### 10.5 Memory Across Sessions
- Long-term memory of user preferences
- "Last time you loved the Negroni - shall I suggest something similar?"

---

## 11. Testing Strategy

### Unit Tests
- Chat model serialization/deserialization
- History trimming logic
- Intent detection accuracy

### Integration Tests
- Full chat flow with mock LLM
- Session persistence and restoration
- Recommendation handoff

### E2E Tests
- Complete conversation flows
- Mobile responsiveness
- Error handling

---

## 12. Migration Path

1. **Phase 1**: Add models and agent config (no UI changes)
2. **Phase 2**: Implement crew and API endpoints
3. **Phase 3**: Add chat template and basic UI
4. **Phase 4**: Integrate with existing cabinet state
5. **Phase 5**: Polish UI and add streaming
