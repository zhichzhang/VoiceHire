# app/server/models/session.py

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.server.models.candidate import (
    CandidateProfile,
)
from app.server.models.experience_evidence import (
    ExperienceEvidence,
)
from app.server.models.resume import CandidateResume
from app.server.models.Interview_turn import (
    InterviewTurn,
)
from app.server.models.evaluation import (
    InterviewEvaluation,
)


class InterviewSession(BaseModel):
    """
    Persistent interview session state.
    """

    session_id: str = Field(
        description="Unique session identifier."
    )

    current_phase: str = Field(
        description="Current active phase."
    )

    status: str = Field(
        default="active",
        description=(
            "Current session status such as active, "
            "processing, completed, expired, or failed."
        ),
    )

    current_question: str | None = Field(
        default=None,
        description="Most recently generated question awaiting an answer."
    )

    current_answer: str | None = Field(
        default=None,
        description=(
            "Most recently submitted answer that is still "
            "being processed."
        )
    )

    turns: list[InterviewTurn] = Field(
        default_factory=list,
        description="All interview turns."
    )

    candidate_profile: CandidateProfile = Field(
        default_factory=CandidateProfile,
        description="Candidate context."
    )

    experience_evidence: ExperienceEvidence = Field(
        default_factory=ExperienceEvidence,
        description="Collected experience evidence."
    )

    evaluation: InterviewEvaluation | None = Field(
        default=None,
        description="Final evaluation result."
    )

    resume_context: CandidateResume | None = Field(
        default=None,
        description=(
            "Structured resume data loaded before "
            "interview start."
        )
    )

    started_at: datetime | None = Field(
        default=None,
        description="Interview start timestamp."
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Interview completion timestamp."
    )

    expires_at: datetime | None = Field(
        default=None,
        description="Session expiration timestamp."
    )