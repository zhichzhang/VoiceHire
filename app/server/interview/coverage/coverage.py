# app/server/interview/coverage/coverage.py

from pydantic import BaseModel, Field


class CoverageResult(BaseModel):
    """
    Result of evaluating information coverage for a phase.

    Coverage is used exclusively for workflow control
    and phase transitions.

    It does not represent candidate performance or
    interview quality.
    """

    score: float = Field(
        ge=0,
        le=1,
        description="Percentage of required information currently collected."
    )

    complete: bool = Field(
        description="Whether the phase completion threshold has been satisfied."
    )

    covered_fields: list[str] = Field(
        default_factory=list,
        description="Fields that have already been collected."
    )

    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields that are still missing and should be targeted by future questions."
    )


class IntroCoverage(BaseModel):
    """
    Tracks information coverage for the intro phase.

    The intro phase focuses on collecting enough
    candidate context to support downstream experience
    selection and question generation.
    """

    most_recent_role: bool = Field(
        default=False,
        description="Whether the candidate's most recent role has been collected."
    )

    education: bool = Field(
        default=False,
        description="Whether educational background has been collected."
    )

    highlighted_experiences: bool = Field(
        default=False,
        description="Whether highlighted experiences have been collected."
    )

    domain_keywords: bool = Field(
        default=False,
        description="Whether domain keywords have been collected."
    )

    other_context: bool = Field(
        default=False,
        description="Whether additional contextual information has been collected."
    )


class ExperienceCoverage(BaseModel):
    """
    Tracks information coverage for the experience phase.

    The experience phase focuses on collecting enough
    evidence to support professional evaluation.
    """

    experience_name: bool = Field(
        default=False,
        description="Whether the experience being discussed has been identified."
    )

    what: bool = Field(
        default=False,
        description="Whether the candidate has explained what they worked on."
    )

    why: bool = Field(
        default=False,
        description="Whether the candidate has explained why the work was needed."
    )

    how: bool = Field(
        default=False,
        description="Whether the candidate has explained how the work was carried out."
    )

    challenge: bool = Field(
        default=False,
        description="Whether major challenges have been discussed."
    )

    outcome: bool = Field(
        default=False,
        description="Whether outcomes, achievements, or impact have been discussed."
    )


class CoverageEvaluator:
    """
    Utility class responsible for converting extracted
    interview information into workflow coverage metrics.

    Coverage evaluation determines:

    - Missing information
    - Coverage percentage
    - Phase completion eligibility
    """

    @staticmethod
    def calculate_score(coverage: BaseModel) -> float:
        values = list(coverage.model_dump().values())

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def evaluate_intro(
        coverage: IntroCoverage,
        threshold: float,
    ) -> CoverageResult:
        score = CoverageEvaluator.calculate_score(
            coverage
        )

        covered_fields = [
            k
            for k, v in coverage.model_dump().items()
            if v
        ]

        missing_fields = [
            k
            for k, v in coverage.model_dump().items()
            if not v
        ]

        return CoverageResult(
            score=score,
            complete=score >= threshold,
            covered_fields=covered_fields,
            missing_fields=missing_fields,
        )

    @staticmethod
    def evaluate_experience(
        coverage: ExperienceCoverage,
        threshold: float,
    ) -> CoverageResult:
        score = CoverageEvaluator.calculate_score(
            coverage
        )

        covered_fields = [
            k
            for k, v in coverage.model_dump().items()
            if v
        ]

        missing_fields = [
            k
            for k, v in coverage.model_dump().items()
            if not v
        ]

        return CoverageResult(
            score=score,
            complete=score >= threshold,
            covered_fields=covered_fields,
            missing_fields=missing_fields,
        )