# app/server/interview/engines/evaluation_engine.py

from __future__ import annotations

from typing import Any

from app.server.core.logger import logger
from app.server.interview.contracts.rubics import (
    EXPERIENCE_WEIGHTS,
    INTERVIEW_WEIGHTS,
    INTRO_WEIGHTS,
)
from app.server.interview.repositories.evaluation_repository import (
    EvaluationRepository,
)
from app.server.llm.client import LLMClient
from app.server.llm.contracts.prompt_outputs import (
    InterviewFeedbackResult,
    PhaseEvaluationResult,
)
from app.server.models.evaluation import (
    CommunicationMetrics,
    DimensionScore,
    InterviewEvaluation,
    PhaseEvaluation,
)
from app.server.models.session import InterviewSession


class EvaluationEngine:
    """
    Aggregates interview evidence and produces
    the final interview evaluation report.

    Responsibilities:
    - aggregate communication metrics from turn assessments
    - generate phase-level evaluation results
    - generate final LLM feedback
    - persist the final evaluation
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def evaluate(
        self,
        session: InterviewSession,
    ) -> InterviewEvaluation:
        """
        Generate the final interview report for a completed session.
        """
        logger.workflow(
            f"[EVALUATION] START session={session.session_id}"
        )
        logger.debug(
            f"[EVALUATION] turn_count={len(session.turns)}"
        )

        communication_metrics = self._evaluate_communication_metrics(session)
        communication_score = self._score_communication(communication_metrics)

        logger.debug(
            "[EVALUATION] COMMUNICATION_METRICS=\n"
            + communication_metrics.model_dump_json(indent=2)
        )
        logger.workflow(
            f"[EVALUATION] communication_score={communication_score:.2f}"
        )

        phase_results = await self._evaluate_phase_results(
            session,
            communication_metrics=communication_metrics,
        )
        professional_score = self._score_professional(phase_results)

        logger.workflow(
            f"[EVALUATION] professional_score={professional_score:.2f}"
        )

        overall_score = (
            communication_score * 0.3
            + professional_score * 0.7
        )

        logger.workflow(
            f"[EVALUATION] overall_score={overall_score:.2f}"
        )

        transcript = [
            turn.model_dump()
            for turn in session.turns
        ]

        logger.debug(
            f"[EVALUATION] transcript_turns={len(transcript)}"
        )

        final_context = {
            "candidate_profile": session.candidate_profile,

            "experience_evidence": session.experience_evidence,

            "phase_evaluations": [
                result.model_dump()
                for result in phase_results
            ],

            "communication_metrics": communication_metrics,

            # 新增
            "interview_transcript": transcript,

            "interview_evaluation": {
                "phase_results": [
                    result.model_dump()
                    for result in phase_results
                ],
                "communication_metrics": communication_metrics.model_dump(),
                "communication_score": communication_score,
                "professional_score": professional_score,
                "overall_score": overall_score,
                "transcript": transcript,
            },
        }

        logger.workflow(
            "[EVALUATION] GENERATE_FINAL_FEEDBACK"
        )

        feedback_result: InterviewFeedbackResult = (
            await self.llm.generate_final_evaluation(final_context)
        )

        logger.debug(
            "[EVALUATION] FEEDBACK_RESULT=\n"
            + feedback_result.model_dump_json(
                indent=2,
                exclude_none=True,
            )
        )

        evaluation = InterviewEvaluation(
            phase_results=phase_results,
            communication_metrics=communication_metrics,
            communication_score=communication_score,
            professional_score=professional_score,
            overall_score=overall_score,
            assessment_confidence=feedback_result.assessment_confidence,
            llm_feedback=feedback_result.llm_feedback,
        )

        logger.database(
            f"[EVALUATION] UPSERT_EVALUATION session={session.session_id}"
        )

        EvaluationRepository.upsert(
            session.session_id,
            evaluation.model_dump(),
        )

        logger.success(
            f"[EVALUATION] COMPLETE session={session.session_id}"
        )

        return evaluation

    def _evaluate_communication_metrics(
        self,
        session: InterviewSession,
    ) -> CommunicationMetrics:
        """
        Aggregate relevance / clarity / fluency across all turns.
        """
        logger.workflow(
            "[EVALUATION] COMPUTE_COMMUNICATION_METRICS"
        )

        if not session.turns:
            logger.warning(
                "[EVALUATION] NO_TURNS_FOUND"
            )
            return CommunicationMetrics(
                relevance=0.0,
                clarity=0.0,
                fluency=0.0,
            )

        relevance_scores = [
            turn.assessment.relevance
            for turn in session.turns
        ]
        clarity_scores = [
            turn.assessment.clarity
            for turn in session.turns
        ]
        fluency_scores = [
            turn.assessment.fluency
            for turn in session.turns
        ]

        logger.debug(
            f"[EVALUATION] relevance_samples={len(relevance_scores)}"
        )
        logger.debug(
            f"[EVALUATION] clarity_samples={len(clarity_scores)}"
        )
        logger.debug(
            f"[EVALUATION] fluency_samples={len(fluency_scores)}"
        )

        return CommunicationMetrics(
            relevance=sum(relevance_scores) / len(relevance_scores),
            clarity=sum(clarity_scores) / len(clarity_scores),
            fluency=sum(fluency_scores) / len(fluency_scores),
        )

    def _score_communication(
        self,
        metrics: CommunicationMetrics,
    ) -> float:
        """
        Convert communication metrics into a 0-100 score.
        """
        return (
            metrics.relevance * 0.4
            + metrics.clarity * 0.3
            + metrics.fluency * 0.3
        ) * 100

    async def _evaluate_phase_results(
        self,
        session: InterviewSession,
        communication_metrics: CommunicationMetrics,
    ) -> list[PhaseEvaluation]:
        """
        Generate phase-level rubric evaluations from the full session.
        """
        phase_results: list[PhaseEvaluation] = []

        for phase_name in ("intro", "experience"):
            logger.workflow(
                f"[EVALUATION] PHASE_START {phase_name}"
            )

            rubric = self._get_rubric_for_phase(phase_name)

            context = {
                "phase_name": phase_name,
                "rubric": self._rubric_to_payload(rubric),
                "candidate_profile": session.candidate_profile,
                "experience_evidence": session.experience_evidence,
                "communication_metrics": communication_metrics,
                "dimensions": self._dimension_specs(rubric),
                "interview_transcript": [
                    turn.model_dump()
                    for turn in session.turns
                    if turn.phase == phase_name
                ],
            }

            logger.debug(
                f"[EVALUATION] phase={phase_name} "
                f"transcript_turns={len(context['interview_transcript'])}"
            )

            logger.workflow(
                f"[EVALUATION] CALL_LLM {phase_name}"
            )

            result: PhaseEvaluationResult = await self.llm.evaluate_phase(context)

            logger.debug(
                "[EVALUATION] PHASE_RESULT=\n"
                + result.model_dump_json(
                    indent=2,
                    exclude_none=True,
                )
            )

            phase_results.append(
                PhaseEvaluation(
                    phase_name=result.phase_name,
                    dimensions=[
                        DimensionScore.model_validate(
                            dimension.model_dump()
                        )
                        for dimension in result.dimensions
                    ],
                    overall_score=result.overall_score,
                    strengths=result.strengths,
                    improvements=result.improvements,
                )
            )

            logger.workflow(
                f"[EVALUATION] PHASE_DONE "
                f"{phase_name} score={result.overall_score:.2f}"
            )

        logger.workflow(
            f"[EVALUATION] PHASE_EVALUATIONS_DONE count={len(phase_results)}"
        )

        return phase_results

    def _score_professional(
        self,
        phase_results: list[PhaseEvaluation],
    ) -> float:
        """
        Aggregate phase scores into a professional competency score.

        Uses INTERVIEW_WEIGHTS and renormalizes if any phase is missing.
        """
        logger.workflow(
            "[EVALUATION] COMPUTE_PROFESSIONAL_SCORE"
        )

        phase_score_map = {
            phase.phase_name: phase.overall_score
            for phase in phase_results
        }

        logger.debug(
            f"[EVALUATION] phase_score_map={phase_score_map}"
        )

        weighted_sum = 0.0
        total_weight = 0.0

        for phase_name, weight in INTERVIEW_WEIGHTS.items():
            if phase_name in phase_score_map:
                weighted_sum += phase_score_map[phase_name] * weight
                total_weight += weight

        logger.debug(
            f"[EVALUATION] weighted_sum={weighted_sum:.2f} "
            f"total_weight={total_weight:.2f}"
        )

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    @staticmethod
    def _get_rubric_for_phase(phase_name: str) -> dict[Any, float]:
        if phase_name == "intro":
            return INTRO_WEIGHTS

        if phase_name == "experience":
            return EXPERIENCE_WEIGHTS

        return {}

    @staticmethod
    def _rubric_to_payload(rubric: dict[Any, float]) -> dict[str, float]:
        return {
            getattr(key, "value", str(key)): value
            for key, value in rubric.items()
        }

    @staticmethod
    def _dimension_specs(rubric: dict[Any, float]) -> list[dict[str, Any]]:
        return [
            {
                "name": getattr(key, "value", str(key)),
                "weight": value,
            }
            for key, value in sorted(
                rubric.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]