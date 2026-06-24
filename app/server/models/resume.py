# app/server/models/resume.py

from pydantic import BaseModel, Field


class ResumeEducation(BaseModel):
    """
    Educational background loaded from the
    candidate's stored resume.
    """

    institution: str = Field(
        description="Educational institution."
    )

    program: str | None = Field(
        default=None,
        description="Degree, major, or academic program."
    )

    timeframe: str | None = Field(
        default=None,
        description="Attendance period."
    )

    status: str | None = Field(
        default=None,
        description="Current academic status."
    )


class ResumeExperience(BaseModel):
    """
    Professional, academic, project, or research
    experience loaded from the candidate's resume.
    """

    name: str = Field(
        description="Experience name."
    )

    organization: str | None = Field(
        default=None,
        description="Company, school, lab, or organization."
    )

    experience_type: str | None = Field(
        default=None,
        description=(
            "internship, full_time, project, "
            "research, startup, open_source, or other."
        )
    )

    timeframe: str | None = Field(
        default=None,
        description="Time period associated with the experience."
    )

    summary: str = Field(
        description="Short summary of the experience."
    )

    skills: list[str] = Field(
        default_factory=list,
        description="Skills or technologies associated with the experience."
    )


class CandidateResume(BaseModel):
    """
    Structured resume data loaded before the
    interview session starts.

    This model represents the system's prior
    knowledge of the candidate and should not
    be confused with CandidateProfile, which
    represents information collected during
    the interview itself.
    """

    education: list[
        ResumeEducation
    ] = Field(
        default_factory=list,
        description="Educational history."
    )

    experiences: list[
        ResumeExperience
    ] = Field(
        default_factory=list,
        description="Experience history."
    )

    skills: list[str] = Field(
        default_factory=list,
        description="Resume skills."
    )