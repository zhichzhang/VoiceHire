# app/server/interview/contracts/prompt_inputs.py

from typing import Literal

from pydantic import BaseModel, Field

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.coverage.coverage import CoverageResult
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume


class IntroQuestionPromptInput(BaseModel):
    candidate_profile: CandidateProfile = Field(
        description="Current candidate profile accumulated during the interview."
    )
    coverage: CoverageResult = Field(
        description="Current intro-phase coverage result."
    )
    previous_questions: list[str] = Field(
        default_factory=list,
        description="Previously asked intro questions."
    )
    previous_answers: list[str] = Field(
        default_factory=list,
        description="Previously given intro answers."
    )


class IntroExtractionPromptInput(BaseModel):
    answer: str = Field(
        description="Candidate's raw self-introduction answer."
    )
    resume_context: CandidateResume | None = Field(
        default=None,
        description="Structured resume context loaded before the interview."
    )
    current_profile: CandidateProfile | None = Field(
        default=None,
        description="Current candidate profile before applying the new extraction result."
    )


class ExperienceQuestionPromptInput(BaseModel):
    mode: Literal["collection", "deep_dive"] = Field(
        description="Question generation mode for the experience phase."
    )
    candidate_profile: CandidateProfile = Field(
        description="Current candidate profile accumulated during the interview."
    )
    experience_evidence: ExperienceEvidence = Field(
        description="Current experience evidence collected so far."
    )
    coverage: CoverageResult | None = Field(
        default=None,
        description="Current experience-phase coverage result, used in collection mode."
    )
    dimensions: list[str] | None = Field(
        default=None,
        description="Evaluation dimensions to target, used in deep_dive mode."
    )
    previous_questions: list[str] = Field(
        default_factory=list,
        description="Previously asked experience questions."
    )
    previous_answers: list[str] = Field(
        default_factory=list,
        description="Previously given experience answers."
    )


class ExperienceExtractionPromptInput(BaseModel):
    answer: str = Field(
        description="Candidate's raw answer to an experience question."
    )
    candidate_profile: CandidateProfile | None = Field(
        default=None,
        description="Current candidate profile before applying the extraction result."
    )
    resume_context: CandidateResume | None = Field(
        default=None,
        description="Structured resume context loaded before the interview."
    )
    experience_context: str | None = Field(
        default=None,
        description="The specific experience currently being discussed."
    )

class ResumeNormalizationPromptInput(BaseModel):
    raw_resume_text: str = Field(
        description="Candidate's pasted resume text."
    )
    name: str = Field(
        description="Candidate name."
    )
    email: str = Field(
        description="Candidate email."
    )
    current_resume_context: CandidateResume | None = Field(
        default=None,
        description=(
            "Existing normalized resume context for this candidate, "
            "if one already exists."
        )
    )

class TurnAssessmentPromptInput(BaseModel):
    phase: PhaseType = Field(
        description="Interview phase for this turn."
    )

    question: str = Field(
        description="The question that was asked."
    )

    answer: str = Field(
        description="Candidate's answer to the question."
    )

