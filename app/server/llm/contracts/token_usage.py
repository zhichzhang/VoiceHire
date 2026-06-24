# app/server/llm/contracts/token_usage.py

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """
    Token consumption reported by an LLM provider.

    These values are provider-agnostic and are used for:

    - Usage analytics
    - Cost tracking
    - Performance monitoring

    The usage object intentionally contains only
    provider metadata and should not contain
    workflow-specific information.
    """

    prompt_tokens: int = Field(
        default=0,
        description="Number of prompt tokens."
    )

    completion_tokens: int = Field(
        default=0,
        description="Number of completion tokens."
    )

    total_tokens: int = Field(
        default=0,
        description="Total tokens consumed."
    )