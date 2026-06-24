# app/server/models/assessment.py

from pydantic import BaseModel, Field


class TurnAssessment(BaseModel):
    """
    Assessment of a single candidate response.

    These metrics are used for interview evaluation
    and do not affect workflow progression.
    """

    relevance: float = Field(
        ge=0,
        le=1,
        description=(
            "How well the answer addresses the question."
        )
    )

    clarity: float = Field(
        ge=0,
        le=1,
        description=(
            "How clear and understandable the answer is."
        )
    )

    fluency: float = Field(
        ge=0,
        le=1,
        description=(
            "How naturally and smoothly the answer is delivered."
        )
    )