# app/server/interview/phases/experience_phase.py

from __future__ import annotations

from app.server.core.logger import logger
from app.server.interview.coverage.coverage import (
    CoverageEvaluator,
    CoverageResult,
    ExperienceCoverage,
)
from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.evaluators.turn_evaluators import TurnEvaluator
from app.server.interview.phases.base_phase import InterviewPhase
from app.server.interview.repositories.evidence_repository import (
    EvidenceRepository,
)
from app.server.interview.repositories.turn_repository import (
    TurnRepository,
)
from app.server.llm.client import LLMClient
from app.server.llm.contracts.prompt_inputs import (
    ExperienceExtractionPromptInput,
    ExperienceQuestionPromptInput,
)
from app.server.llm.contracts.prompt_outputs import (
    ExperienceExtractionResult,
    QuestionGenerationResult,
)
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.assessment import TurnAssessment
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.session import InterviewSession


class ExperiencePhase(InterviewPhase):
    """
    Experience phase implementation.

    Responsibilities:
    - Generate collection / deep-dive questions
    - Extract structured evidence from answers
    - Merge extracted evidence into session state
    - Persist evidence and turn history
    - Evaluate coverage for phase completion

    Completion rules:
    - coverage reaches threshold, OR
    - number of experience turns reaches max_turns
    """

    phase_name = PhaseType.EXPERIENCE
    max_turns = 5
    coverage_threshold = 0.8

    def __init__(
        self,
        llm: LLMClient,
        turn_evaluator: TurnEvaluator | None = None,
    ):
        self.llm = llm
        self.turn_evaluator = turn_evaluator

    async def generate_question(
        self,
        session: InterviewSession,
    ) -> QuestionGenerationResult:
        """
        Generate the next experience question.

        Strategy:
        - First experience turn: collection mode
        - Later turns: deep-dive mode
        """
        coverage = await self.evaluate_coverage(session)

        logger.workflow(
            f"[EXPERIENCE] GENERATE_QUESTION "
            f"session={session.session_id}"
        )

        logger.debug(
            "[EXPERIENCE] COVERAGE=\n"
            + coverage.model_dump_json(indent=2)
        )

        previous_questions, previous_answers = self._get_previous_turn_history(
            session
        )
        turn_count = self._phase_turn_count(session)

        logger.debug(
            f"[EXPERIENCE] TURN_COUNT={turn_count}"
        )

        if turn_count == 0 or not session.experience_evidence.experience_name:
            logger.workflow(
                "[EXPERIENCE] MODE=collection"
            )

            result = await self.llm.generate_experience_question(
                ExperienceQuestionPromptInput(
                    mode="collection",
                    candidate_profile=session.candidate_profile,
                    experience_evidence=session.experience_evidence,
                    coverage=coverage,
                    previous_questions=previous_questions,
                    previous_answers=previous_answers,
                )
            )
        else:
            dimensions = self._select_deep_dive_dimensions(
                session.experience_evidence
            )

            logger.workflow(
                "[EXPERIENCE] MODE=deep_dive"
            )

            logger.debug(
                f"[EXPERIENCE] DIMENSIONS={dimensions}"
            )

            result = await self.llm.generate_experience_deep_dive_question(
                ExperienceQuestionPromptInput(
                    mode="deep_dive",
                    candidate_profile=session.candidate_profile,
                    experience_evidence=session.experience_evidence,
                    dimensions=dimensions,
                    previous_questions=previous_questions,
                    previous_answers=previous_answers,
                )
            )

        phase_label = self._phase_label()
        if result.phase != phase_label:
            result = result.model_copy(
                update={"phase": phase_label}
            )

        logger.workflow(
            f"[EXPERIENCE] QUESTION={result.question}"
        )

        session.current_question = result.question
        return result

    async def process_answer(
        self,
        session: InterviewSession,
        answer: str,
    ) -> None:
        """
        Process the candidate's experience answer.

        This:
        - extracts structured experience evidence
        - merges it into the session evidence
        - persists the updated evidence
        - records a completed turn in session state and the database
        """
        logger.workflow(
            f"[EXPERIENCE] PROCESS_ANSWER "
            f"session={session.session_id}"
        )

        logger.debug(
            f"[EXPERIENCE] ANSWER={answer[:500]}"
        )

        session.current_answer = answer

        extraction = await self.llm.extract_experience(
            ExperienceExtractionPromptInput(
                answer=answer,
                candidate_profile=session.candidate_profile,
                resume_context=session.resume_context,
                experience_context=self._resolve_experience_context(session),
            )
        )

        logger.debug(
            "[EXPERIENCE] EXTRACTION=\n"
            + extraction.model_dump_json(
                indent=2,
                exclude_none=True,
            )
        )

        merged_evidence = self._merge_experience_evidence(
            session.experience_evidence,
            extraction,
        )

        session.experience_evidence = merged_evidence

        logger.debug(
            "[EXPERIENCE] EVIDENCE_AFTER_MERGE=\n"
            + merged_evidence.model_dump_json(
                indent=2,
                exclude_none=True,
            )
        )

        logger.database(
            f"[EXPERIENCE] UPSERT_EVIDENCE "
            f"session={session.session_id}"
        )

        EvidenceRepository.upsert(
            session.session_id,
            merged_evidence.model_dump(),
        )

        question = self._resolve_current_question(session)
        # turn_number = self._phase_turn_count(session) + 1
        turn_number = self._next_turn_number(session)
        phase_label = self._phase_label()

        placeholder_assessment = TurnAssessment(
            relevance=0.0,
            clarity=0.0,
            fluency=0.0,
        )

        turn = InterviewTurn(
            turn_number=turn_number,
            phase=phase_label,
            question=question,
            answer=answer,
            assessment=placeholder_assessment,
        )

        session.turns.append(turn)

        logger.workflow(
            f"[EXPERIENCE] TURN_ADDED "
            f"turn={turn_number}"
        )

        logger.database(
            f"[EXPERIENCE] INSERT_TURN "
            f"turn={turn_number}"
        )

        TurnRepository.add_turn(
            session_id=session.session_id,
            turn_number=turn_number,
            phase=phase_label,
            question=question,
            answer=answer,
            relevance=placeholder_assessment.relevance,
            clarity=placeholder_assessment.clarity,
            fluency=placeholder_assessment.fluency,
        )

        session.current_question = None
        session.current_answer = None

        logger.workflow(
            "[EXPERIENCE] PROCESS_ANSWER_DONE"
        )

    async def evaluate_coverage(
        self,
        session: InterviewSession,
    ) -> CoverageResult:
        evidence = session.experience_evidence

        coverage = ExperienceCoverage()

        coverage.experience_name = (
            evidence.experience_name is not None
        )

        coverage.what = (
            evidence.what is not None
        )

        coverage.why = (
            evidence.why is not None
        )

        coverage.how = (
            evidence.how is not None
        )

        coverage.challenge = (
            evidence.challenge is not None
        )

        coverage.outcome = (
            evidence.outcome is not None
        )

        result = CoverageEvaluator.evaluate_experience(
            coverage,
            self.coverage_threshold,
        )

        logger.debug(
            "[EXPERIENCE] COVERAGE_RESULT=\n"
            + result.model_dump_json(indent=2)
        )

        return result

    def _merge_experience_evidence(
        self,
        current_evidence: ExperienceEvidence,
        extracted: ExperienceExtractionResult,
    ) -> ExperienceEvidence:
        """
        Merge extracted experience data into the current evidence.

        Rules:
        - Prefer newly extracted scalar values when present.
        - Preserve existing values when the extractor returns null.
        """
        return current_evidence.model_copy(
            update={
                "experience_type": (
                    extracted.experience_type
                    or current_evidence.experience_type
                ),
                "experience_name": (
                    extracted.experience_name
                    or current_evidence.experience_name
                ),
                "what": (
                    extracted.what
                    or current_evidence.what
                ),
                "why": (
                    extracted.why
                    or current_evidence.why
                ),
                "how": (
                    extracted.how
                    or current_evidence.how
                ),
                "challenge": (
                    extracted.challenge
                    or current_evidence.challenge
                ),
                "outcome": (
                    extracted.outcome
                    or current_evidence.outcome
                ),
            }
        )

    def _resolve_current_question(
        self,
        session: InterviewSession,
    ) -> str:
        """
        Resolve the question that should be associated with the answer.

        Preference order:
        1. The pending question stored on the session
        2. The latest stored turn question in the session
        3. A safe fallback for the first experience answer
        """
        if session.current_question:
            return session.current_question

        if session.turns:
            return session.turns[-1].question

        return "Tell me about one experience from your resume."

    def _resolve_experience_context(
        self,
        session: InterviewSession,
    ) -> str | None:
        """
        Resolve the active experience context for extraction.
        """
        evidence = session.experience_evidence
        if evidence.experience_name:
            return evidence.experience_name

        if session.resume_context and session.resume_context.experiences:
            first_exp = session.resume_context.experiences[0]
            if first_exp.name and first_exp.organization:
                return f"{first_exp.name} at {first_exp.organization}"
            return first_exp.name or first_exp.organization

        return None

    def _get_previous_turn_history(
        self,
        session: InterviewSession,
    ) -> tuple[list[str], list[str]]:
        """
        Extract previous experience questions and answers from session turns.
        """
        experience_turns = [
            turn
            for turn in session.turns
            if turn.phase == self.phase_name
        ]

        previous_questions = [
            turn.question
            for turn in experience_turns
        ]

        previous_answers = [
            turn.answer
            for turn in experience_turns
        ]

        return previous_questions, previous_answers

    def _phase_label(self) -> str:
        """
        Convert the phase identifier into a plain string label.
        """
        return getattr(self.phase_name, "value", self.phase_name)

    def _phase_turn_count(self, session: InterviewSession) -> int:
        """
        Count how many turns have already been recorded in this phase.
        """
        return sum(
            1
            for turn in session.turns
            if turn.phase == self._phase_label()
        )

    @staticmethod
    def _select_deep_dive_dimensions(
        evidence: ExperienceEvidence,
    ) -> list[str]:
        """
        Pick the most relevant deep-dive dimensions based on missing evidence.

        Preference order:
        - problem_solving
        - impact
        - ownership
        - domain_expertise
        """
        dimensions: list[str] = []

        if evidence.challenge is None:
            dimensions.append("problem_solving")

        if evidence.outcome is None:
            dimensions.append("impact")

        if evidence.what is None or evidence.experience_name is None:
            dimensions.append("ownership")

        if evidence.how is None:
            dimensions.append("domain_expertise")

        if not dimensions:
            dimensions = [
                "problem_solving",
                "impact",
                "ownership",
                "domain_expertise",
            ]

        deduped: list[str] = []
        seen: set[str] = set()
        for dimension in dimensions:
            if dimension not in seen:
                deduped.append(dimension)
                seen.add(dimension)

        return deduped

    async def is_complete(self, session: InterviewSession) -> bool:
        experience_turn_count = len([
            turn for turn in session.turns
            if turn.phase == self._phase_label()
        ])

        if experience_turn_count < 2:
            return False

        coverage = await self.evaluate_coverage(session)

        return coverage.complete or experience_turn_count >= self.max_turns