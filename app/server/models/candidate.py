# app/server/models/candidate.py

from pydantic import BaseModel, Field

from app.server.llm.contracts.prompt_outputs import EducationContext, HighlightedExperience


class CandidateProfile(BaseModel):
    """
    Candidate context accumulated throughout
    the interview.
    """

    most_recent_role: str | None = Field(
        default=None,
        description="Most recent professional role."
    )

    education: EducationContext | None = Field(
        default=None,
        description="Most relevant educational background."
    )

    highlighted_experiences: list[
        HighlightedExperience
    ] = Field(
        default_factory=list,
        description="Experiences emphasized by the candidate."
    )

    domain_keywords: list[str] = Field(
        default_factory=list,
        description="Top domain keywords."
    )

    other_context: list[str] = Field(
        default_factory=list,
        description="Additional contextual information."
    )