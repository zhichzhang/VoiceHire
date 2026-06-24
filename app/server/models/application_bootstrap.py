# app/server/models/application_bootstrap.py

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession


class ResumeUpsertDecision(StrEnum):
    """
    Decision made during resume preflight and onboarding.

    This decision controls whether the onboarding flow:
    - reuses an existing resume
    - normalizes and updates the resume with the LLM
    - rejects the pasted text as a mismatch
    """

    USE_EXISTING = "use_existing"
    NORMALIZE_UPDATE = "normalize_update"
    REJECT_MISMATCH = "reject_mismatch"


class ResumePreflightResult(BaseModel):
    """
    Result of the resume preflight check.

    This result is produced before calling the LLM normalization step.
    It is used to decide whether the system should reuse an existing resume,
    normalize and update the resume, or reject the input as a mismatch.
    """

    decision: ResumeUpsertDecision = Field(
        description="Final onboarding decision for the pasted resume."
    )
    extracted_emails: list[str] = Field(
        default_factory=list,
        description="Email addresses extracted from the pasted resume text."
    )
    extracted_name: str | None = Field(
        default=None,
        description="Candidate name inferred from the pasted resume text, if available."
    )
    matched_sections: list[str] = Field(
        default_factory=list,
        description="Resume section keywords that were matched during preflight."
    )
    section_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="How strongly the pasted text looks like a resume based on section keyword matches."
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable reasons explaining the preflight decision."
    )


class ApplicationBootstrapResult(BaseModel):
    """
    Final result of application onboarding.

    This object bundles the candidate record, resume record, and the
    initialized interview session returned after onboarding completes.
    """

    candidate: dict[str, object] = Field(
        description="Persisted candidate record."
    )
    resume: dict[str, object] = Field(
        description="Persisted resume record."
    )
    session: InterviewSession = Field(
        description="Initialized interview session."
    )
    normalized_resume: CandidateResume = Field(
        description="Normalized resume structure used for persistence."
    )
    is_new_candidate: bool = Field(
        description="Whether this onboarding created a new candidate record."
    )
    resume_updated: bool = Field(
        description="Whether the resume was normalized and written back to storage."
    )
    used_existing_resume: bool = Field(
        description="Whether the system reused an existing resume without updating it."
    )