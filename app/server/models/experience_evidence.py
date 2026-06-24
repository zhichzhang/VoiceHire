# app/server/models/experience_evidence.py

from pydantic import BaseModel, Field


class ExperienceEvidence(BaseModel):
    """
    Structured evidence collected from the
    experience phase.
    """

    experience_type: str | None = Field(
        default=None,
        description="Type of experience."
    )

    experience_name: str | None = Field(
        default=None,
        description="Name of the experience."
    )

    what: str | None = Field(
        default=None,
        description="What the candidate worked on."
    )

    why: str | None = Field(
        default=None,
        description="Why the work was necessary."
    )

    how: str | None = Field(
        default=None,
        description="How the work was carried out."
    )

    challenge: str | None = Field(
        default=None,
        description="Major challenge encountered."
    )

    outcome: str | None = Field(
        default=None,
        description="Result, achievement, or impact."
    )