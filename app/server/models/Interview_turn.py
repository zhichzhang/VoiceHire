# app/server/models/Interview_turn.py

from pydantic import BaseModel, Field

from app.server.models.assessment import (
    TurnAssessment,
)


from datetime import datetime

from pydantic import BaseModel, Field

from app.server.models.assessment import (
    TurnAssessment,
)


class InterviewTurn(BaseModel):
    """
    Represents a single interview interaction.
    """

    turn_number: int | None = Field(
        default=None,
        description="Sequential turn number within the session."
    )

    phase: str = Field(
        description="Interview phase."
    )

    question: str = Field(
        description="Question asked by the interviewer."
    )

    answer: str = Field(
        description="Answer provided by the candidate."
    )

    assessment: TurnAssessment = Field(
        description="Communication assessment assigned to the answer."
    )

    assessment_status: str = Field(
        default="pending",
        description=(
            "Turn assessment lifecycle status. "
            "Expected values: pending, processing, completed, or failed."
        )
    )

    assessment_error: str | None = Field(
        default=None,
        description=(
            "Error message recorded when asynchronous turn scoring fails."
        )
    )

    assessed_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp when turn assessment completed "
            "or failed."
        )
    )