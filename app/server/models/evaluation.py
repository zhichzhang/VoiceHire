# app/server/models/evaluation.py

from pydantic import BaseModel, Field

from app.server.models.interview_feedback import (
    LLMInterviewFeedback,
)


class CommunicationMetrics(BaseModel):
    """
    Aggregated communication metrics across
    all interview turns.
    """

    relevance: float = Field(
        ge=0,
        le=1,
        description="Average relevance score."
    )

    clarity: float = Field(
        ge=0,
        le=1,
        description="Average clarity score."
    )

    fluency: float = Field(
        ge=0,
        le=1,
        description="Average fluency score."
    )


class DimensionScore(BaseModel):
    """
    Score for a single evaluation dimension.
    """

    name: str = Field(
        description="Dimension name."
    )

    score: float = Field(
        ge=0,
        le=100,
        description="Dimension score."
    )

    justification: str = Field(
        description="Reason for the score."
    )


class PhaseEvaluation(BaseModel):
    """
    Evaluation result for a single phase.
    """

    phase_name: str = Field(
        description="Phase name."
    )

    dimensions: list[
        DimensionScore
    ] = Field(
        default_factory=list,
        description="Dimension scores."
    )

    overall_score: float = Field(
        ge=0,
        le=100,
        description="Overall phase score."
    )

    strengths: list[str] = Field(
        default_factory=list,
        description="Phase strengths."
    )

    improvements: list[str] = Field(
        default_factory=list,
        description="Phase improvement areas."
    )


class InterviewEvaluation(BaseModel):
    """
    Final interview evaluation.
    """

    phase_results: list[
        PhaseEvaluation
    ] = Field(
        default_factory=list,
        description="Results from all interview phases."
    )

    communication_metrics: CommunicationMetrics = Field(
        description="Aggregated communication metrics."
    )

    communication_score: float = Field(
        ge=0,
        le=100,
        description="Communication score."
    )

    professional_score: float = Field(
        ge=0,
        le=100,
        description="Professional competency score."
    )

    overall_score: float = Field(
        ge=0,
        le=100,
        description="Final interview score."
    )

    assessment_confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence level of the assessment."
    )

    llm_feedback: LLMInterviewFeedback | None = Field(
        default=None,
        description="Human-readable interview feedback."
    )