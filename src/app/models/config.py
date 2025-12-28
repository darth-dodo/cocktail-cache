"""Pydantic models for YAML configuration validation.

These models validate agent, task, and LLM configurations
loaded from YAML files in the agents/config directory.
"""

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a CrewAI agent.

    Defines the persona and behavior settings for an agent
    including role, goal, and backstory.
    """

    role: str = Field(
        ...,
        description="The agent's role title (e.g., 'Drink Recommender')",
    )
    goal: str = Field(
        ...,
        description="The agent's primary objective",
    )
    backstory: str = Field(
        ...,
        description="Background context that shapes the agent's behavior",
    )
    verbose: bool = Field(
        default=False,
        description="Whether to enable verbose logging for this agent",
    )
    allow_delegation: bool = Field(
        default=False,
        description="Whether this agent can delegate tasks to other agents",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "role": "Drink Recommender",
                "goal": "Find the best drinks based on available ingredients",
                "backstory": "You are an expert mixologist...",
                "verbose": False,
                "allow_delegation": False,
            }
        }


class TaskConfig(BaseModel):
    """Configuration for a CrewAI task.

    Defines the task description, expected output format,
    and optional output model for structured responses.
    """

    description: str = Field(
        ...,
        description="Detailed description of what the task should accomplish",
    )
    expected_output: str = Field(
        ...,
        description="Description of the expected output format",
    )
    output_model: str | None = Field(
        default=None,
        description="Name of the Pydantic model for structured output",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Analyze the user's cabinet and recommend drinks",
                "expected_output": "A ranked list of drink recommendations",
                "output_model": "RecipeOutput",
            }
        }


class LLMConfig(BaseModel):
    """Configuration for an LLM profile.

    Defines model settings including the model identifier,
    token limits, and temperature for creativity control.
    """

    model: str = Field(
        ...,
        description="LLM model identifier (e.g., 'anthropic/claude-3-5-haiku-20241022')",
    )
    max_tokens: int = Field(
        ...,
        gt=0,
        le=32768,
        description="Maximum tokens in the response",
    )
    temperature: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, higher = more creative)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "anthropic/claude-3-5-haiku-20241022",
                "max_tokens": 4096,
                "temperature": 0.7,
            }
        }
