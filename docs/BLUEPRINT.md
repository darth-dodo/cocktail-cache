# Multi-Agent AI Service Blueprint

A best practices guide and template for building production-ready multi-agent AI services using Python, FastAPI, CrewAI, and Redis.

**Based on patterns from Pocket Portals** - a D&D adventure generator with 280+ tests and proven architecture.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Project Structure](#project-structure)
3. [Configuration Patterns](#configuration-patterns)
4. [State Management](#state-management)
5. [Agent Architecture](#agent-architecture)
6. [API Design](#api-design)
7. [Streaming Responses](#streaming-responses)
8. [Error Handling](#error-handling)
9. [Content Safety](#content-safety)
10. [Cost Optimization](#cost-optimization)
11. [Testing Strategies](#testing-strategies)
12. [Agentic Development Workflow](#agentic-development-workflow)
13. [Pre-commit Hooks](#pre-commit-hooks)
14. [CI/CD Pipeline](#cicd-pipeline)
15. [Observability & Debugging](#observability--debugging)
16. [Prompt Engineering](#prompt-engineering)
17. [Development Workflow](#development-workflow)
18. [Deployment](#deployment)
19. [Checklist](#checklist)

---

## Philosophy

### Core Principles

1. **LLM for Content, Code for Logic**
   - Use LLMs for creative/narrative generation
   - Use deterministic code for business rules, validation, routing
   - Never let LLMs make decisions that should be predictable

2. **Configuration Over Code**
   - Agent personalities, constraints, and behavior live in config files
   - Changing behavior shouldn't require code changes
   - Prompts are configuration, not hardcoded strings

3. **Type Safety Everywhere**
   - The LLM is unpredictable; everything else shouldn't be
   - Pydantic models for all state and API contracts
   - Enums for finite state values

4. **Graceful Degradation**
   - Systems should work (degraded) when dependencies fail
   - Always have fallbacks for external services
   - Log warnings, don't crash

5. **Minimize LLM Calls**
   - Each call costs money and adds latency
   - Batch where possible, cache where appropriate
   - Pre-compute what you can

---

## Project Structure

```
my-ai-service/
├── src/
│   ├── __init__.py
│   ├── settings.py              # Global settings singleton
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI app, routes, lifespan
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Optional: BaseAgent class
│   │   ├── primary_agent.py     # Main content generator
│   │   ├── specialist_agent.py  # Domain-specific agent
│   │   └── chaos_agent.py       # Optional: randomness/variety
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── router.py            # Agent routing logic
│   │   ├── executor.py          # Turn/request execution
│   │   ├── flow.py              # CrewAI Flow orchestration
│   │   └── flow_state.py        # Flow state model
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── models.py            # Core Pydantic models
│   │   ├── session_manager.py   # Session orchestration
│   │   └── backends/
│   │       ├── __init__.py
│   │       ├── base.py          # SessionBackend Protocol
│   │       ├── memory.py        # InMemoryBackend
│   │       ├── redis.py         # RedisBackend
│   │       └── factory.py       # create_backend()
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py            # YAML config loader
│   │   ├── settings.py          # Pydantic Settings
│   │   ├── agents.yaml          # Agent definitions
│   │   └── tasks.yaml           # Task templates
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── templates.py         # Static data/templates
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Utility functions
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_models.py
│   ├── test_router.py
│   ├── test_agents.py
│   ├── test_backends.py
│   ├── test_session_manager.py
│   └── test_api.py
│
├── static/                      # Frontend assets (if applicable)
├── docs/
│   ├── architecture-diagrams.md
│   └── guides/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── README.md
└── render.yaml                  # Deployment config
```

### Key Conventions

- **Singular imports**: Export key classes in `__init__.py`
- **Flat when possible**: Avoid deep nesting
- **Co-locate tests**: Mirror src/ structure in tests/
- **Separate concerns**: Each module has one responsibility

---

## Configuration Patterns

### Environment Variables (`src/config/settings.py`)

```python
"""Application settings using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Required
    anthropic_api_key: str

    # Session backend
    session_backend: str = "redis"  # "redis" or "memory"
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 86400  # 24 hours

    # Server
    environment: str = "development"  # "development", "staging", "production", or "test"
    host: str = "0.0.0.0"
    port: int = 8000

    # CrewAI Configuration
    crewai_tracing: bool = False  # Enable flow tracing for debugging

    # LLM defaults
    default_model: str = "anthropic/claude-3-5-haiku-20241022"
    default_temperature: float = 0.7
    default_max_tokens: int = 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### Agent Configuration (`src/config/agents.yaml`)

```yaml
# Agent definitions - behavior lives here, not in code
# ============================================================
# CONTENT RATING: Define your content policy here
# ============================================================

defaults:
  llm:
    model: "anthropic/claude-3-5-haiku-20241022"
    temperature: 0.7
    max_tokens: 1024

primary_agent:
  role: "Primary Agent"
  goal: "Generate high-quality content for the user"
  backstory: |
    You are an expert at [domain]. Your responses are:
    - Concise (50-100 words)
    - Actionable
    - Professional

    CONSTRAINTS:
    - Never exceed 150 words
    - Always provide specific examples
    - End with a clear next step

    FORBIDDEN:
    - Marketing language ("amazing", "revolutionary")
    - Vague advice ("it depends")
    - Apologies for limitations
  verbose: false
  allow_delegation: false
  llm:
    temperature: 0.7
    max_tokens: 1024
  memory: true

specialist_agent:
  role: "Domain Specialist"
  goal: "Provide expert analysis in specific domain"
  backstory: |
    You handle technical details. Be precise and brief.

    VOICE:
    - Use exact numbers and specifics
    - Keep responses under 30 words when possible
    - Facts, not opinions
  verbose: false
  allow_delegation: false
  llm:
    temperature: 0.3  # Lower for more deterministic output
    max_tokens: 256
  memory: false
```

### Config Loader (`src/config/loader.py`)

```python
"""YAML configuration loader with Pydantic models."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM configuration."""
    model: str = "anthropic/claude-3-5-haiku-20241022"
    temperature: float = 0.7
    max_tokens: int = 1024


class AgentConfig(BaseModel):
    """Agent configuration from YAML."""
    role: str
    goal: str
    backstory: str
    verbose: bool = False
    allow_delegation: bool = False
    llm: LLMConfig = LLMConfig()
    memory: bool = False


class TaskConfig(BaseModel):
    """Task template configuration."""
    description: str
    expected_output: str


@lru_cache
def _load_yaml(filename: str) -> dict[str, Any]:
    """Load and cache YAML file."""
    config_dir = Path(__file__).parent
    filepath = config_dir / filename
    with open(filepath) as f:
        return yaml.safe_load(f)


def load_agent_config(agent_name: str) -> AgentConfig:
    """Load agent configuration by name."""
    data = _load_yaml("agents.yaml")
    defaults = data.get("defaults", {})
    agent_data = data.get(agent_name, {})

    # Merge defaults with agent-specific config
    merged = {**defaults, **agent_data}
    if "llm" in defaults and "llm" in agent_data:
        merged["llm"] = {**defaults["llm"], **agent_data["llm"]}

    return AgentConfig(**merged)


def load_task_config(task_name: str) -> TaskConfig:
    """Load task template by name."""
    data = _load_yaml("tasks.yaml")
    return TaskConfig(**data[task_name])
```

---

## State Management

### Core Models (`src/state/models.py`)

```python
"""Core state models using Pydantic."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ServicePhase(str, Enum):
    """Service phases for routing decisions."""
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"


class SessionState(BaseModel):
    """Main session state container.

    Design principles:
    - All fields have sensible defaults
    - Validators ensure data integrity
    - Nested models for complex structures
    """

    session_id: str
    phase: ServicePhase = ServicePhase.ONBOARDING
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    current_options: list[str] = Field(default_factory=list)
    user_profile: Any = None  # Your domain-specific model
    metadata: dict[str, Any] = Field(default_factory=dict)
    recent_agents: list[str] = Field(default_factory=list)

    @field_validator("conversation_history")
    @classmethod
    def limit_history(cls, v: list) -> list:
        """Keep only last N exchanges to manage context size."""
        max_history = 20
        return v[-max_history:] if len(v) > max_history else v

    @model_validator(mode="after")
    def validate_state_consistency(self) -> "SessionState":
        """Ensure state is internally consistent."""
        # Add your validation logic
        return self

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "SessionState":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)
```

### Backend Protocol (`src/state/backends/base.py`)

```python
"""Abstract base for session backends."""

from typing import Protocol, runtime_checkable

from src.state.models import SessionState


@runtime_checkable
class SessionBackend(Protocol):
    """Protocol defining session storage operations.

    Using Protocol enables structural subtyping without inheritance.
    All methods are async to support both in-memory and I/O-bound backends.
    """

    async def create(self, session_id: str, state: SessionState) -> None:
        """Create a new session."""
        ...

    async def get(self, session_id: str) -> SessionState | None:
        """Get session by ID, or None if not found."""
        ...

    async def update(self, session_id: str, state: SessionState) -> None:
        """Update existing session."""
        ...

    async def delete(self, session_id: str) -> bool:
        """Delete session, return True if existed."""
        ...

    async def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        ...
```

### In-Memory Backend (`src/state/backends/memory.py`)

```python
"""In-memory session backend for development/testing."""

from src.state.models import SessionState


class InMemoryBackend:
    """Simple dict-based session storage."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    async def create(self, session_id: str, state: SessionState) -> None:
        self._sessions[session_id] = state

    async def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    async def update(self, session_id: str, state: SessionState) -> None:
        if session_id in self._sessions:
            self._sessions[session_id] = state

    async def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def exists(self, session_id: str) -> bool:
        return session_id in self._sessions
```

### Redis Backend (`src/state/backends/redis.py`)

```python
"""Redis session backend for production."""

import redis.asyncio as redis

from src.state.models import SessionState


class RedisBackend:
    """Redis-based session storage with TTL support."""

    def __init__(self, redis_url: str, ttl: int = 86400) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl
        self._prefix = "session:"

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    async def create(self, session_id: str, state: SessionState) -> None:
        await self._redis.setex(
            self._key(session_id),
            self._ttl,
            state.to_json(),
        )

    async def get(self, session_id: str) -> SessionState | None:
        data = await self._redis.get(self._key(session_id))
        if data:
            return SessionState.from_json(data)
        return None

    async def update(self, session_id: str, state: SessionState) -> None:
        # Preserve TTL on update
        await self._redis.setex(
            self._key(session_id),
            self._ttl,
            state.to_json(),
        )

    async def delete(self, session_id: str) -> bool:
        result = await self._redis.delete(self._key(session_id))
        return result > 0

    async def exists(self, session_id: str) -> bool:
        return await self._redis.exists(self._key(session_id)) > 0

    async def close(self) -> None:
        """Close Redis connection."""
        await self._redis.close()
```

### Backend Factory (`src/state/backends/factory.py`)

```python
"""Backend factory with graceful fallback."""

import logging

from src.config.settings import get_settings
from src.state.backends.base import SessionBackend
from src.state.backends.memory import InMemoryBackend
from src.state.backends.redis import RedisBackend

logger = logging.getLogger(__name__)


async def create_backend() -> SessionBackend:
    """Create backend based on settings with graceful fallback."""
    settings = get_settings()

    if settings.session_backend == "memory":
        logger.info("Using in-memory session backend")
        return InMemoryBackend()

    # Try Redis
    try:
        backend = RedisBackend(
            redis_url=settings.redis_url,
            ttl=settings.redis_session_ttl,
        )
        # Test connection
        await backend._redis.ping()
        logger.info("Using Redis session backend")
        return backend
    except Exception as e:
        logger.warning(
            f"Failed to connect to Redis: {e}. "
            "Falling back to in-memory backend."
        )
        return InMemoryBackend()
```

---

## Agent Architecture

### Agent Base Pattern (`src/agents/primary_agent.py`)

```python
"""Primary agent - main content generator."""

from crewai import LLM, Agent, Task

from src.config.loader import load_agent_config, load_task_config
from src.settings import settings


class PrimaryAgent:
    """Primary content generation agent."""

    def __init__(self) -> None:
        """Initialize agent from YAML config."""
        config = load_agent_config("primary_agent")

        self.llm = LLM(
            model=config.llm.model,
            api_key=settings.anthropic_api_key,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

        self.agent = Agent(
            role=config.role,
            goal=config.goal,
            backstory=config.backstory,
            verbose=config.verbose,
            allow_delegation=config.allow_delegation,
            llm=self.llm,
        )

    def respond(self, action: str, context: str = "") -> str:
        """Generate response to user action.

        Args:
            action: User's input/action
            context: Accumulated conversation context

        Returns:
            Agent's response text
        """
        task_config = load_task_config("primary_response")

        description = task_config.description.format(action=action)
        if context:
            description = f"{context}\n\nCurrent input: {description}"

        task = Task(
            description=description,
            expected_output=task_config.expected_output,
            agent=self.agent,
        )

        result = task.execute_sync()
        return str(result)
```

### Agent Router (`src/engine/router.py`)

```python
"""Agent routing logic."""

import random
from dataclasses import dataclass

from src.state.models import ServicePhase


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    agents: list[str]
    include_optional: bool
    reason: str


class AgentRouter:
    """Routes requests to appropriate agents based on context.

    Design principles:
    - Deterministic core logic
    - Controlled randomness where appropriate
    - Clear reasoning for decisions
    """

    # Keywords that trigger specialist agent
    SPECIALIST_KEYWORDS = [
        "analyze", "calculate", "compare", "measure",
        "technical", "specific", "details", "data",
    ]

    # Probability and cooldown for optional agent
    OPTIONAL_AGENT_PROBABILITY = 0.15
    OPTIONAL_AGENT_COOLDOWN = 3

    def route(
        self,
        action: str,
        phase: ServicePhase,
        recent_agents: list[str],
    ) -> RoutingDecision:
        """Route action to appropriate agents.

        Args:
            action: User's action text
            phase: Current service phase
            recent_agents: Recently used agents for cooldown tracking

        Returns:
            RoutingDecision with agents list and reasoning
        """
        agents = []
        reasons = []

        # Phase-based routing
        if phase == ServicePhase.ONBOARDING:
            return RoutingDecision(
                agents=["onboarding_agent"],
                include_optional=False,
                reason="Onboarding phase - dedicated agent",
            )

        # Always include primary agent for active phase
        agents.append("primary_agent")
        reasons.append("Primary agent for main response")

        # Check for specialist keywords
        action_lower = action.lower()
        if any(kw in action_lower for kw in self.SPECIALIST_KEYWORDS):
            agents.append("specialist_agent")
            reasons.append("Specialist keywords detected")

        # Optional agent with probability and cooldown
        include_optional = self._should_include_optional(recent_agents)
        if include_optional:
            reasons.append("Optional agent included (random)")

        return RoutingDecision(
            agents=agents,
            include_optional=include_optional,
            reason=" | ".join(reasons),
        )

    def _should_include_optional(self, recent_agents: list[str]) -> bool:
        """Determine if optional agent should be included."""
        # Check cooldown
        if "optional_agent" in recent_agents[-self.OPTIONAL_AGENT_COOLDOWN:]:
            return False

        # Random probability
        return random.random() < self.OPTIONAL_AGENT_PROBABILITY
```

### CrewAI Flow (`src/engine/flow.py`)

```python
"""Multi-agent orchestration using CrewAI Flows."""

from typing import Any

from crewai.flow.flow import Flow, listen, router, start

from src.engine.flow_state import FlowState
from src.engine.router import AgentRouter, RoutingDecision
from src.state.models import ServicePhase


class ServiceFlow(Flow[FlowState]):
    """Orchestrates multi-agent execution.

    Flow pattern:
    1. @start() - Entry point, routing
    2. @listen(start) - Execute agents
    3. @router(execute) - Check success/error
    4. @listen("success") - Aggregate results
    5. @listen("error") - Handle failures
    """

    DEFAULT_OPTIONS = ["Continue", "Ask a question", "Start over"]

    def __init__(self, primary: Any, specialist: Any, optional: Any) -> None:
        super().__init__()
        self.agents = {
            "primary_agent": primary,
            "specialist_agent": specialist,
            "optional_agent": optional,
        }
        self.router = AgentRouter()

    @start()
    def route_action(self) -> FlowState:
        """Entry point - determine which agents to invoke."""
        if self.state.agents_to_invoke:
            return self.state  # Routing already provided

        phase = ServicePhase(self.state.phase)
        routing = self.router.route(
            action=self.state.action,
            phase=phase,
            recent_agents=self.state.recent_agents,
        )

        self.state.agents_to_invoke = routing.agents.copy()
        self.state.include_optional = routing.include_optional
        self.state.routing_reason = routing.reason

        return self.state

    @listen(route_action)
    def execute_agents(self) -> FlowState:
        """Execute each agent and collect responses."""
        try:
            accumulated_context = self.state.context

            for agent_name in self.state.agents_to_invoke:
                agent = self.agents[agent_name]
                response = agent.respond(
                    action=self.state.action,
                    context=accumulated_context,
                )
                self.state.responses[agent_name] = response

                # Accumulate context for subsequent agents
                accumulated_context = self._accumulate_context(
                    accumulated_context, agent_name, response
                )

            # Optional agent sees all context
            if self.state.include_optional:
                optional_response = self.agents["optional_agent"].respond(
                    action=self.state.action,
                    context=accumulated_context,
                )
                self.state.responses["optional_agent"] = optional_response

            return self.state

        except Exception as e:
            self.state.error = f"Agent execution failed: {str(e)}"
            return self.state

    def _accumulate_context(
        self, context: str, agent_name: str, response: str
    ) -> str:
        """Build context with previous agent responses."""
        label = agent_name.replace("_", " ").title()
        if context:
            return f"{context}\n\n[{label} responded]: {response}"
        return f"[{label} responded]: {response}"

    @router(execute_agents)
    def check_status(self) -> str:
        """Route based on execution success."""
        return "error" if self.state.error else "success"

    @listen("success")
    def aggregate_responses(self) -> FlowState:
        """Combine all responses into final output."""
        parts = []

        for agent_name in self.state.agents_to_invoke:
            if agent_name in self.state.responses:
                parts.append(self.state.responses[agent_name])

        if self.state.include_optional and "optional_agent" in self.state.responses:
            parts.append(self.state.responses["optional_agent"])

        self.state.output = "\n\n".join(parts)
        return self.state

    @listen("error")
    def handle_error(self) -> FlowState:
        """Handle errors gracefully."""
        self.state.output = (
            "I encountered an issue processing your request. "
            f"Error: {self.state.error}"
        )
        self.state.options = self.DEFAULT_OPTIONS
        return self.state

    @listen(aggregate_responses)
    def generate_options(self) -> FlowState:
        """Generate contextual next options."""
        # Could ask an agent for contextual options
        # For now, use defaults
        self.state.options = self.DEFAULT_OPTIONS
        return self.state
```

---

## API Design

### FastAPI Application (`src/api/main.py`)

```python
"""FastAPI application with lifespan management."""

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.primary_agent import PrimaryAgent
from src.agents.specialist_agent import SpecialistAgent
from src.agents.optional_agent import OptionalAgent
from src.engine import AgentRouter, ServiceExecutor
from src.state import SessionManager
from src.state.backends import create_backend


# Request/Response Models
class ActionRequest(BaseModel):
    """Request model for user actions."""
    action: str | None = None
    option_index: int | None = Field(default=None, ge=1, le=5)
    session_id: str | None = None


class ServiceResponse(BaseModel):
    """Standard response model."""
    output: str
    session_id: str
    options: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    environment: str


# Global state
primary_agent: PrimaryAgent | None = None
specialist_agent: SpecialistAgent | None = None
optional_agent: OptionalAgent | None = None
executor: ServiceExecutor | None = None
router = AgentRouter()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Initialize resources on startup, cleanup on shutdown."""
    global primary_agent, specialist_agent, optional_agent, executor

    # Initialize backend and session manager
    backend = await create_backend()
    app.state.backend = backend
    app.state.session_manager = SessionManager(backend)

    # Initialize agents if API key available
    if os.getenv("ANTHROPIC_API_KEY"):
        primary_agent = PrimaryAgent()
        specialist_agent = SpecialistAgent()
        optional_agent = OptionalAgent()
        executor = ServiceExecutor(
            primary=primary_agent,
            specialist=specialist_agent,
            optional=optional_agent,
        )

    yield

    # Cleanup
    if hasattr(backend, "close"):
        await backend.close()


app = FastAPI(
    title="My AI Service",
    description="Multi-agent AI service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for development
if os.getenv("ENVIRONMENT", "development") == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def get_session_manager(request: Request) -> SessionManager:
    """Get session manager from app state."""
    return request.app.state.session_manager


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        environment=os.getenv("ENVIRONMENT", "development"),
    )


@app.get("/start", response_model=ServiceResponse)
async def start_session(request: Request) -> ServiceResponse:
    """Start a new session."""
    sm = get_session_manager(request)
    state = await sm.create_session()

    return ServiceResponse(
        output="Welcome! How can I help you today?",
        session_id=state.session_id,
        options=["Get started", "Learn more", "Ask a question"],
    )


@app.post("/action", response_model=ServiceResponse)
async def process_action(
    request: Request,
    action_request: ActionRequest,
) -> ServiceResponse:
    """Process user action."""
    sm = get_session_manager(request)
    state = await sm.get_or_create_session(action_request.session_id)

    # Resolve action
    if action_request.option_index is not None:
        options = state.current_options or ["Continue", "Help", "Exit"]
        action = options[action_request.option_index - 1]
    else:
        action = action_request.action or ""

    # Content safety filter
    action = filter_content(action)

    if executor is None:
        return ServiceResponse(
            output="Service not available. Check API key.",
            session_id=state.session_id,
            options=["Try again"],
        )

    # Route and execute
    routing = router.route(
        action=action,
        phase=state.phase,
        recent_agents=state.recent_agents,
    )

    context = build_context(state.conversation_history)
    result = await executor.execute_async(
        action=action,
        routing=routing,
        context=context,
    )

    # Update session
    await sm.add_exchange(state.session_id, action, result.output)
    await sm.update_recent_agents(state.session_id, routing.agents)
    await sm.set_options(state.session_id, result.options)

    return ServiceResponse(
        output=result.output,
        session_id=state.session_id,
        options=result.options,
    )


def build_context(history: list[dict[str, str]]) -> str:
    """Format conversation history for context."""
    lines = []
    for turn in history:
        lines.append(f"User: {turn['action']}")
        lines.append(f"Assistant: {turn['response']}")
    return "\n".join(lines)


def filter_content(action: str) -> str:
    """Filter inappropriate content."""
    # Implement your content filtering
    return action
```

---

## Streaming Responses

### SSE Streaming Pattern

```python
"""Server-Sent Events streaming for real-time responses."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Request
from sse_starlette.sse import EventSourceResponse


@app.post("/action/stream")
async def process_action_stream(
    request: Request,
    action_request: ActionRequest,
) -> EventSourceResponse:
    """Process action with streaming response."""

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        try:
            sm = get_session_manager(request)
            state = await sm.get_or_create_session(action_request.session_id)

            # Route
            routing = router.route(
                action=action_request.action,
                phase=state.phase,
                recent_agents=state.recent_agents,
            )

            yield {
                "event": "routing",
                "data": json.dumps({
                    "agents": routing.agents,
                    "reason": routing.reason,
                }),
            }

            accumulated_context = build_context(state.conversation_history)
            output_parts = []

            # Execute each agent
            for agent_name in routing.agents:
                yield {
                    "event": "agent_start",
                    "data": json.dumps({"agent": agent_name}),
                }

                agent = agents[agent_name]

                # Run in executor to not block
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: agent.respond(
                        action=action_request.action,
                        context=accumulated_context,
                    ),
                )

                output_parts.append(response)

                # Stream character by character for typewriter effect
                for char in response:
                    yield {
                        "event": "agent_chunk",
                        "data": json.dumps({
                            "agent": agent_name,
                            "chunk": char,
                        }),
                    }
                    await asyncio.sleep(0.015)  # 15ms delay

                yield {
                    "event": "agent_response",
                    "data": json.dumps({
                        "agent": agent_name,
                        "content": response,
                    }),
                }

                # Accumulate context
                accumulated_context = f"{accumulated_context}\n\n[{agent_name}]: {response}"

            # Final options
            yield {
                "event": "options",
                "data": json.dumps({
                    "options": ["Continue", "Ask more", "Done"],
                }),
            }

            # Update session
            full_output = "\n\n".join(output_parts)
            await sm.add_exchange(state.session_id, action_request.action, full_output)

            yield {
                "event": "complete",
                "data": json.dumps({"session_id": state.session_id}),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

    return EventSourceResponse(event_generator())
```

---

## Error Handling

### Graceful Degradation Pattern

```python
"""Error handling with graceful degradation."""

import logging
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_fallback(fallback_value: T) -> Callable:
    """Decorator for graceful fallback on errors."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"{func.__name__} failed: {e}. Using fallback."
                )
                return fallback_value
        return wrapper
    return decorator


# Usage in agents
class SafeAgent:
    """Agent with built-in error handling."""

    DEFAULT_RESPONSE = "I'm having trouble processing that. Please try again."

    @with_fallback(DEFAULT_RESPONSE)
    def respond(self, action: str, context: str = "") -> str:
        # Your agent logic
        pass


# Backend factory with fallback (already shown above)
async def create_backend() -> SessionBackend:
    """Create backend with graceful fallback."""
    try:
        # Try Redis
        backend = RedisBackend(...)
        await backend._redis.ping()
        return backend
    except Exception as e:
        logger.warning(f"Redis failed: {e}. Using in-memory.")
        return InMemoryBackend()
```

---

## Content Safety

### Content Filtering Pattern

```python
"""Content safety filtering."""

import re
from typing import Callable


# Blocked patterns - customize for your domain
BLOCKED_PATTERNS = [
    # Harmful content
    r"harm\s*(myself|yourself|others)",
    r"(kill|hurt|injure)\s*(myself|yourself)",

    # Inappropriate content
    r"(sexual|explicit|nude)",

    # Add domain-specific patterns
]

SAFE_REDIRECT = "Let's focus on something more constructive."


def filter_content(
    action: str,
    patterns: list[str] = BLOCKED_PATTERNS,
    redirect: str = SAFE_REDIRECT,
) -> str:
    """Filter inappropriate content from input.

    Args:
        action: User input
        patterns: Regex patterns to block
        redirect: Safe redirect message

    Returns:
        Original action if safe, redirect message if blocked
    """
    action_lower = action.lower()

    for pattern in patterns:
        if re.search(pattern, action_lower):
            return redirect

    return action


def create_content_filter(
    blocked_patterns: list[str],
    redirect_message: str,
) -> Callable[[str], str]:
    """Factory for custom content filters."""
    def filter_func(action: str) -> str:
        return filter_content(
            action,
            patterns=blocked_patterns,
            redirect=redirect_message,
        )
    return filter_func
```

---

## Cost Optimization

### Strategies for Minimizing LLM Costs

```python
"""Cost optimization strategies."""

# 1. Use appropriate model sizes
AGENT_CONFIGS = {
    # High-quality output needed - use capable model
    "creative_agent": {
        "model": "claude-3-5-sonnet",
        "max_tokens": 1024,
    },

    # Simple tasks - use fast/cheap model
    "classifier_agent": {
        "model": "claude-3-5-haiku",  # Cheaper, faster
        "max_tokens": 256,
    },
}


# 2. Minimize calls per request
class CombatManager:
    """Example: Combat uses NO LLM calls except final summary."""

    def resolve_attack(self, attacker, defender) -> dict:
        """Pure computation - no LLM."""
        roll = random.randint(1, 20)
        hit = roll + attacker.bonus >= defender.ac
        damage = self.roll_damage() if hit else 0
        return {"hit": hit, "damage": damage, "roll": roll}

    def summarize_combat(self, log: list[str]) -> str:
        """ONE LLM call for entire combat."""
        # This is the only LLM call
        return narrator.summarize(log)


# 3. Cache repeated queries
from functools import lru_cache

@lru_cache(maxsize=100)
def get_static_content(content_type: str) -> str:
    """Cache static/repeated content."""
    return agent.generate(f"Generate {content_type}")


# 4. Batch context efficiently
def build_efficient_context(history: list[dict], max_turns: int = 5) -> str:
    """Limit context to recent history."""
    recent = history[-max_turns:]
    return "\n".join(
        f"User: {t['action']}\nAssistant: {t['response']}"
        for t in recent
    )


# 5. Use templates for predictable outputs
RESPONSE_TEMPLATES = {
    "greeting": "Hello! I'm here to help with {domain}.",
    "error": "I encountered an issue: {error}. Please try again.",
    "not_found": "I couldn't find {item}. Would you like to {alternative}?",
}

def templated_response(template_key: str, **kwargs) -> str:
    """Use template instead of LLM for predictable responses."""
    return RESPONSE_TEMPLATES[template_key].format(**kwargs)
```

---

## Testing Strategies

### Test Structure

```python
"""Testing patterns for AI services."""

import pytest
from unittest.mock import AsyncMock, MagicMock


# 1. Test models independently
class TestSessionState:
    """Test Pydantic models."""

    def test_creates_with_defaults(self):
        state = SessionState(session_id="test-123")
        assert state.phase == ServicePhase.ONBOARDING
        assert state.conversation_history == []

    def test_validates_constraints(self):
        with pytest.raises(ValueError):
            SessionState(session_id="")  # If required

    def test_serializes_to_json_and_back(self):
        original = SessionState(session_id="test-123")
        json_str = original.to_json()
        restored = SessionState.from_json(json_str)
        assert restored.session_id == original.session_id


# 2. Test routing logic (deterministic)
class TestAgentRouter:
    """Test routing decisions."""

    def test_routes_to_specialist_on_keyword(self):
        router = AgentRouter()
        decision = router.route(
            action="analyze this data",
            phase=ServicePhase.ACTIVE,
            recent_agents=[],
        )
        assert "specialist_agent" in decision.agents

    def test_respects_cooldown(self):
        router = AgentRouter()
        # Optional agent in recent history
        recent = ["optional_agent", "primary_agent", "primary_agent"]

        # Should not include optional due to cooldown
        decision = router.route(
            action="test",
            phase=ServicePhase.ACTIVE,
            recent_agents=recent,
        )
        assert not decision.include_optional


# 3. Test backends
class TestInMemoryBackend:
    """Test session backend."""

    @pytest.fixture
    def backend(self):
        return InMemoryBackend()

    @pytest.mark.asyncio
    async def test_create_and_get(self, backend):
        state = SessionState(session_id="test-123")
        await backend.create("test-123", state)

        retrieved = await backend.get("test-123")
        assert retrieved is not None
        assert retrieved.session_id == "test-123"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing(self, backend):
        result = await backend.get("nonexistent")
        assert result is None


# 4. Test API endpoints
class TestAPI:
    """Test FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_start_creates_session(self, client):
        response = client.get("/start")
        assert response.status_code == 200
        assert "session_id" in response.json()


# 5. Mock LLM calls for agent tests
class TestPrimaryAgent:
    """Test agent with mocked LLM."""

    @pytest.fixture
    def mock_agent(self, monkeypatch):
        agent = PrimaryAgent()
        # Mock the task execution
        mock_task = MagicMock()
        mock_task.execute_sync.return_value = "Mocked response"
        monkeypatch.setattr(
            "crewai.Task",
            lambda **kwargs: mock_task,
        )
        return agent

    def test_respond_returns_string(self, mock_agent):
        result = mock_agent.respond("test action")
        assert isinstance(result, str)
        assert len(result) > 0
```

### Test Configuration (`conftest.py`)

```python
"""Shared test fixtures."""

import pytest
from unittest.mock import AsyncMock

from src.state.backends.memory import InMemoryBackend
from src.state.session_manager import SessionManager


@pytest.fixture
def memory_backend():
    """In-memory backend for testing."""
    return InMemoryBackend()


@pytest.fixture
def session_manager(memory_backend):
    """Session manager with memory backend."""
    return SessionManager(memory_backend)


@pytest.fixture
def mock_agent():
    """Mock agent that returns predictable responses."""
    agent = AsyncMock()
    agent.respond.return_value = "Mock response"
    return agent
```

---

## Agentic Development Workflow

Building AI agent systems requires a specific development approach that differs from traditional software development.

### The Agentic TDD Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│                   AGENTIC TDD WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│  1. SCAFFOLD: Define agent config in YAML (behavior spec)       │
│  2. MOCK: Write tests with mocked LLM responses                 │
│  3. INTEGRATE: Connect real agent, verify output shape          │
│  4. PROMPT: Iterate on backstory/constraints until quality      │
│  5. GUARD: Add content safety and validation layers             │
│  6. OBSERVE: Add logging, monitor costs, track failures         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Test the Deterministic Parts First**
   - Router logic, state transitions, validation
   - Mock all LLM calls in unit tests
   - These should have 90%+ coverage

2. **Integration Tests for Agent Behavior**
   - Test that agents return expected structure
   - Validate JSON parsing, fallback handling
   - Can run with real LLM in CI (optional, costly)

3. **Prompt Iteration is Development**
   - YAML configs ARE your code for agent behavior
   - Version control prompt changes like code
   - A/B test prompts using config variants

4. **Cost-Conscious Development**
   ```python
   # Bad: LLM call per unit test
   def test_agent_responds():
       result = agent.respond("test")  # Real LLM call = $$$

   # Good: Mock the LLM layer
   def test_agent_responds(mock_llm):
       mock_llm.return_value = "Mocked response"
       result = agent.respond("test")  # Free
       assert isinstance(result, str)
   ```

5. **Fallback-First Design**
   ```python
   # Every LLM-dependent function needs a fallback
   def generate_quest(self, character: CharacterSheet) -> Quest:
       try:
           result = self.agent.execute_sync()
           return self._parse_quest(result)
       except Exception as e:
           logger.error(f"Quest generation failed: {e}")
           return self._create_fallback_quest(character)  # Always works
   ```

### Development Flow for New Agents

```bash
# 1. Define agent in YAML
# config/agents.yaml
new_agent:
  role: "New Agent Role"
  backstory: |
    Your constraints and personality here.
    Word limit: 50-100 words.

# 2. Create agent class (minimal)
# src/agents/new_agent.py
class NewAgent:
    def __init__(self):
        config = load_agent_config("new_agent")
        self.agent = Agent(role=config.role, ...)

# 3. Write tests with mocks
# tests/test_new_agent.py
def test_respond_returns_string(mock_llm):
    agent = NewAgent()
    mock_llm.return_value = "Test response"
    assert isinstance(agent.respond("test"), str)

# 4. Add to router
# src/engine/router.py
if "keyword" in action.lower():
    agents.append("new_agent")

# 5. Integrate in executor/flow
# 6. Test end-to-end with real LLM
# 7. Monitor costs and quality
```

### Agent Development Checklist

- [ ] Agent defined in `agents.yaml` with word limits
- [ ] Task template defined in `tasks.yaml`
- [ ] Agent class with `respond()` interface
- [ ] Fallback responses for failures
- [ ] Unit tests with mocked LLM
- [ ] Router integration with keywords
- [ ] Integration test with real LLM (optional)
- [ ] Cost monitoring in place

---

## Pre-commit Hooks

Pre-commit hooks ensure code quality before commits reach the repository. This is your first line of defense.

### Complete Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
  # Standard file hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace      # Remove trailing whitespace
      - id: end-of-file-fixer        # Ensure files end with newline
      - id: check-yaml               # Validate YAML syntax
      - id: check-added-large-files  # Prevent large file commits
      - id: check-merge-conflict     # Detect merge conflict markers
      - id: detect-private-key       # Prevent accidental key commits

  # Python linting and formatting with Ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.4
    hooks:
      - id: ruff                     # Linting (replaces flake8, isort, etc.)
        args: [--fix]                # Auto-fix where possible
      - id: ruff-format              # Formatting (replaces black)

  # Type checking with mypy
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-requests
          - types-PyYAML
          - pydantic
        args: [
          --ignore-missing-imports,
          --disable-error-code=misc,
          --disable-error-code=type-arg,
          --disable-error-code=no-any-return
        ]
```

### Installation and Usage

```bash
# Install pre-commit (once per project)
make install  # or: uv run pre-commit install

# Manual run (all files)
uv run pre-commit run --all-files

# Skip hooks temporarily (use sparingly)
git commit --no-verify -m "WIP: work in progress"

# Update hooks to latest versions
uv run pre-commit autoupdate
```

### pyproject.toml Configuration

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "B",   # flake8-bugbear (common bugs)
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade (modern Python)
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=src --cov-report=term-missing"

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

### What Each Hook Catches

| Hook | Catches | Example |
|------|---------|---------|
| trailing-whitespace | Invisible trailing spaces | `line ends here   ` |
| check-yaml | Invalid YAML syntax | Missing colons, bad indentation |
| detect-private-key | Committed secrets | `-----BEGIN RSA PRIV4TE KEY-----` |
| ruff check | Code issues | Unused imports, undefined vars |
| ruff format | Style violations | Inconsistent formatting |
| mypy | Type errors | `str + int`, missing types |

---

## CI/CD Pipeline

Continuous Integration ensures every change passes quality gates before merging.

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run ruff check
        run: uv run ruff check src/ tests/

      - name: Run ruff format check
        run: uv run ruff format --check src/ tests/

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run tests with coverage
        run: uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=70
        env:
          ANTHROPIC_API_KEY: test-key-for-ci  # Fake key for mocked tests

  # Optional: Type checking job
  typecheck:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: uv sync --extra dev
      - run: uv run mypy src/

  # Optional: Integration tests with real LLM
  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: uv sync --extra dev
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Key CI Patterns for AI Services

1. **Mock API Keys for Unit Tests**
   ```yaml
   env:
     ANTHROPIC_API_KEY: test-key-for-ci  # Fake, never hits API
   ```

2. **Real Keys Only for Integration Tests**
   ```yaml
   if: github.event_name == 'push' && github.ref == 'refs/heads/main'
   env:
     ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}  # Real, from secrets
   ```

3. **Coverage Threshold Enforcement**
   ```yaml
   run: uv run pytest --cov-fail-under=70  # Fails if < 70% coverage
   ```

4. **Separate Lint and Test Jobs**
   - Lint runs fast, catches obvious issues
   - Tests run in parallel after lint passes

---

## Observability & Debugging

AI agent systems need specialized observability because failures are often semantic, not just technical.

### Logging Configuration

```python
"""Logging setup for AI service."""

import logging
import sys
from typing import Any

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Reduce noise from libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("crewai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def log_agent_call(
    agent_name: str,
    action: str,
    context_length: int,
    response_length: int,
    duration_ms: float,
) -> None:
    """Log agent invocation with key metrics."""
    logger.info(
        f"Agent: {agent_name} | "
        f"Action: {action[:50]}... | "
        f"Context: {context_length} chars | "
        f"Response: {response_length} chars | "
        f"Duration: {duration_ms:.0f}ms"
    )


def log_routing_decision(
    action: str,
    agents: list[str],
    reason: str,
) -> None:
    """Log routing decisions for debugging."""
    logger.info(
        f"Route: {action[:30]}... -> {agents} | Reason: {reason}"
    )
```

### CrewAI Verbose Mode

```python
# In settings
class Settings(BaseSettings):
    crew_verbose: bool = True  # Enable CrewAI debug output
    log_level: str = "INFO"

# In agent initialization
self.agent = Agent(
    role=config.role,
    goal=config.goal,
    backstory=config.backstory,
    verbose=settings.crew_verbose,  # Logs all LLM interactions
    llm=self.llm,
)
```

### Debugging Agent Failures

```python
"""Patterns for debugging LLM output issues."""

import json
import logging

logger = logging.getLogger(__name__)


def parse_with_debug(raw_output: str, expected_keys: list[str]) -> dict:
    """Parse LLM output with detailed debugging."""

    # Log raw output for debugging
    logger.debug(f"Raw LLM output ({len(raw_output)} chars): {raw_output[:200]}...")

    # Try direct JSON parse
    try:
        result = json.loads(raw_output)
        logger.debug(f"Parsed successfully: {list(result.keys())}")
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed at position {e.pos}: {e.msg}")

    # Try extracting JSON from markdown code blocks
    if "```json" in raw_output:
        json_content = raw_output.split("```json")[1].split("```")[0]
        try:
            result = json.loads(json_content.strip())
            logger.debug("Parsed from markdown code block")
            return result
        except json.JSONDecodeError:
            logger.warning("Markdown JSON extraction failed")

    # Log failure details
    logger.error(
        f"Failed to parse LLM output. "
        f"Expected keys: {expected_keys}. "
        f"Raw output: {raw_output[:500]}"
    )

    return {}  # Return empty dict, let caller handle fallback


# Usage with error context
def generate_quest(self, character: CharacterSheet) -> Quest:
    try:
        result = self.agent.execute_sync()
        quest_data = parse_with_debug(
            str(result),
            expected_keys=["title", "description", "objectives"]
        )

        if not quest_data:
            logger.error(f"Quest generation returned empty for character: {character.name}")
            return self._create_fallback_quest(character)

        return self._create_quest_from_data(quest_data)

    except Exception as e:
        logger.error(f"Quest generation exception: {e}", exc_info=True)
        return self._create_fallback_quest(character)
```

### Cost Tracking

```python
"""Simple cost tracking for LLM calls."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class LLMCostTracker:
    """Track LLM costs per session/request."""

    # Approximate costs per 1K tokens (Claude Haiku)
    INPUT_COST_PER_1K: ClassVar[float] = 0.00025
    OUTPUT_COST_PER_1K: ClassVar[float] = 0.00125

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    call_count: int = 0

    def record_call(self, input_tokens: int, output_tokens: int) -> None:
        """Record a single LLM call."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.call_count += 1

    @property
    def total_cost(self) -> float:
        """Calculate total cost in USD."""
        input_cost = (self.total_input_tokens / 1000) * self.INPUT_COST_PER_1K
        output_cost = (self.total_output_tokens / 1000) * self.OUTPUT_COST_PER_1K
        return input_cost + output_cost

    def summary(self) -> str:
        """Get cost summary."""
        return (
            f"Calls: {self.call_count} | "
            f"Tokens: {self.total_input_tokens}in/{self.total_output_tokens}out | "
            f"Cost: ${self.total_cost:.4f}"
        )
```

---

## Prompt Engineering

The prompts in your YAML configs are where agent behavior is defined. This is code.

### Prompt Structure Best Practices

```yaml
# config/agents.yaml

narrator:
  role: "Narrator"
  goal: "Create immersive, concise scene descriptions"
  backstory: |
    # IDENTITY
    You are a master storyteller for solo D&D adventures.

    # CONSTRAINTS (Most Important - Put First)
    THE TIGHTNESS RULES:
    - 40-80 words per response (hard limit: 100)
    - One sense per beat - don't stack sight+sound+smell
    - No "You see..." or "You hear..." - just describe it
    - End with something actionable, not a question

    # STYLE GUIDE
    VOICE:
    - Second person, present tense ("You step into...")
    - Active verbs, concrete nouns
    - Specific details over vague descriptions

    # FORBIDDEN (Explicit Blocklist)
    NEVER:
    - Ask questions back to the player
    - Use passive voice
    - Say "seems to be" or "appears to"
    - Exceed 100 words under any circumstances

    # EXAMPLES (If Needed)
    Good: "The tavern door groans. Firelight catches the bartender's scar."
    Bad: "You see a tavern with a door that seems old. It appears there might be a bartender inside who has some kind of scar."
```

### Key Prompt Patterns

1. **Word Limits in Backstory**
   ```yaml
   backstory: |
     Keep responses between 40-80 words. Hard limit: 100.
   ```
   - Put limits FIRST in the prompt
   - Use both soft and hard limits
   - Be specific about counting method

2. **Explicit Forbidden List**
   ```yaml
   FORBIDDEN:
     - Never say "I cannot..."
     - Never apologize for limitations
     - Never break character
   ```
   - LLMs respond well to explicit "NEVER" lists
   - Be specific about anti-patterns

3. **Show Don't Tell with Examples**
   ```yaml
   Good: "Steel clashes. Blood sprays. The goblin crumples."
   Bad: "There is a combat scene where the player fights a goblin."
   ```
   - Examples are worth 1000 words of instruction
   - Show both good AND bad examples

4. **Role Separation**
   ```yaml
   keeper:
     backstory: |
       You handle MECHANICS ONLY:
       - Dice rolls and modifiers
       - Success/failure outcomes
       - Combat resolution

       You do NOT:
       - Describe scenes (that's the Narrator)
       - Add commentary (that's the Jester)
       - Give quest details (that's the Innkeeper)
   ```
   - Clear boundaries prevent agents stepping on each other

5. **Temperature Tuning**
   ```yaml
   narrator:
     llm:
       temperature: 0.7  # Creative, varied responses

   keeper:
     llm:
       temperature: 0.3  # More deterministic, consistent
   ```
   - High temp (0.7-1.0): Creative content
   - Low temp (0.1-0.4): Structured/mechanical output

### Task Template Patterns

```yaml
# config/tasks.yaml

narrate_scene:
  description: |
    The player has taken this action: {action}

    Describe what happens next in 40-80 words.
    Focus on sensory details and consequences.
    End with something the player can act on.
  expected_output: |
    A vivid, concise scene description that:
    - Responds directly to the player's action
    - Uses sensory language
    - Is 40-80 words (max 100)
    - Ends with an actionable hook

resolve_action:
  description: |
    Resolve this action mechanically: {action}
    Difficulty: {difficulty}

    Roll appropriate dice. Report success/failure briefly.
    Format: "[Roll]: 1d20+X = Y (success/failure)"
  expected_output: |
    A brief mechanical resolution in 10-20 words.
    Include the dice roll, total, and outcome.
```

### Prompt Testing Strategy

```python
"""Test prompts produce expected output shapes."""

import pytest

class TestPromptQuality:
    """Test that prompts produce quality output."""

    def test_narrator_word_count(self, narrator_agent):
        """Narrator should respect word limits."""
        response = narrator_agent.respond("I enter the tavern")
        word_count = len(response.split())

        # Allow some flexibility but enforce hard limit
        assert word_count <= 120, f"Response too long: {word_count} words"

    def test_narrator_no_questions(self, narrator_agent):
        """Narrator should not ask questions."""
        response = narrator_agent.respond("I look around")

        assert "?" not in response, "Narrator should not ask questions"

    def test_keeper_includes_dice(self, keeper_agent):
        """Keeper should include dice notation."""
        response = keeper_agent.resolve_action("I attack the goblin")

        assert "d20" in response.lower() or "1d" in response, \
            "Keeper should mention dice rolls"
```

---

## Development Workflow

### Makefile

```makefile
.PHONY: install dev test lint format check clean docker-dev

# Setup
install:
	uv sync
	uv run pre-commit install

# Development
dev:
	uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8888

# Testing
test:
	uv run pytest -v --cov=src --cov-report=term-missing

test-fast:
	uv run pytest -x -v

test-cov:
	uv run pytest --cov=src --cov-report=html
	open htmlcov/index.html

# Quality
lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

check: lint test
	@echo "All checks passed!"

# Docker
docker-dev:
	docker-compose up --build

docker-down:
	docker-compose down

docker-clean:
	docker-compose down -v --rmi local

# Cleanup
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Pre-commit Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```

---

## Deployment

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Production image
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment
COPY --from=builder /app/.venv .venv

# Copy application
COPY src/ src/
COPY static/ static/

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8888:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SESSION_BACKEND=redis
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - ./src:/app/src:ro  # Hot reload in dev

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

## Checklist

### Project Setup
- [ ] Project structure matches blueprint
- [ ] Environment variables documented in `.env.example`
- [ ] Makefile with standard commands
- [ ] Pre-commit hooks configured (all 6 hooks)
- [ ] Docker and docker-compose ready
- [ ] GitHub Actions CI/CD pipeline

### Configuration
- [ ] Pydantic Settings for environment
- [ ] YAML configs for agents and tasks
- [ ] Config loader with caching
- [ ] Defaults merged with overrides
- [ ] `crew_verbose` setting for debugging

### State Management
- [ ] Pydantic models for all state
- [ ] SessionBackend Protocol defined
- [ ] InMemoryBackend for development
- [ ] RedisBackend for production
- [ ] Factory with graceful fallback

### Agents
- [ ] Agents load config from YAML
- [ ] Word limits defined in backstory (FIRST in prompt)
- [ ] Temperature tuned per agent role
- [ ] Context accumulation between agents
- [ ] Fallback responses for every LLM-dependent function
- [ ] FORBIDDEN list in backstory

### Routing
- [ ] AgentRouter with clear logic
- [ ] Keyword-based specialist routing
- [ ] Optional agent with probability/cooldown
- [ ] Deterministic core, controlled randomness

### API
- [ ] FastAPI with lifespan management
- [ ] Request/Response Pydantic models
- [ ] Health check endpoint
- [ ] Session management via app.state
- [ ] Content safety filtering

### Streaming
- [ ] SSE endpoint for real-time delivery
- [ ] Character-by-character streaming
- [ ] Event types: routing, agent_start, chunk, response, complete

### Error Handling
- [ ] Graceful degradation patterns
- [ ] Fallback values for failures
- [ ] Error logging without crashes
- [ ] User-friendly error messages

### Testing
- [ ] Models tested independently
- [ ] Routing logic tested (deterministic)
- [ ] Backends tested with async
- [ ] API endpoints tested
- [ ] Agents tested with mocked LLM (not real calls)
- [ ] 70%+ coverage target (enforced in CI)
- [ ] Fake API key in CI for unit tests

### Agentic Development
- [ ] Follow Agentic TDD cycle (Scaffold → Mock → Integrate → Prompt → Guard → Observe)
- [ ] Test deterministic parts first (90%+ coverage)
- [ ] Mock LLM calls in unit tests (cost-conscious)
- [ ] Prompt iteration tracked in version control
- [ ] Agent development checklist completed per agent

### Pre-commit & CI
- [ ] All 6 pre-commit hooks active
- [ ] `ruff check` and `ruff format` configured
- [ ] `mypy` with appropriate settings
- [ ] CI runs lint and test on every PR
- [ ] Coverage threshold enforced (`--cov-fail-under=70`)
- [ ] Integration tests with real LLM (main branch only, optional)

### Observability
- [ ] Logging configured (reduce library noise)
- [ ] Agent calls logged with metrics (action, duration, response size)
- [ ] Routing decisions logged
- [ ] LLM output parsing includes debug info
- [ ] Cost tracking in place

### Prompt Engineering
- [ ] Constraints FIRST in backstory
- [ ] Word limits with soft and hard thresholds
- [ ] FORBIDDEN list for anti-patterns
- [ ] Good/Bad examples in prompts
- [ ] Role separation between agents
- [ ] Temperature tuned per agent type

### Cost Optimization
- [ ] Appropriate model sizes per agent (Haiku for simple, Sonnet for complex)
- [ ] Minimize LLM calls per request
- [ ] Cache repeated queries
- [ ] Efficient context management
- [ ] Templates for predictable outputs
- [ ] Cost tracker for monitoring spend

### Documentation
- [ ] README with setup instructions
- [ ] Architecture diagrams
- [ ] API documentation (auto-generated)
- [ ] Best practices guide (this document)

---

## Quick Start Template

```bash
# Clone this blueprint
git clone https://github.com/your-org/ai-service-blueprint.git my-service
cd my-service

# Setup
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

make install
make dev

# Visit http://localhost:8888
```

---

*This blueprint is based on patterns proven in production with 280+ tests and comprehensive coverage.*
