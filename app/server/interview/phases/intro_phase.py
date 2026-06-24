from __future__ import annotations

from app.server.core.logger import logger
from app.server.interview.coverage.coverage import (
    CoverageEvaluator,
    CoverageResult,
    IntroCoverage,
)
from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.evaluators.turn_evaluators import TurnEvaluator
from app.server.interview.phases.base_phase import InterviewPhase
from app.server.interview.repositories.profile_repository import (
    ProfileRepository,
)
from app.server.interview.repositories.turn_repository import (
    TurnRepository,
)
from app.server.llm.client import LLMClient
from app.server.llm.contracts.prompt_inputs import (
    IntroExtractionPromptInput,
    IntroQuestionPromptInput,
)
from app.server.llm.contracts.prompt_outputs import (
    IntroExtractionResult,
    QuestionGenerationResult,
)
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.assessment import TurnAssessment
from app.server.models.candidate import CandidateProfile
from app.server.models.session import InterviewSession


class IntroPhase(InterviewPhase):
    """
    Intro phase implementation.

    Responsibilities:
    - Generate the first / next intro question
    - Extract structured candidate context from the answer
    - Merge extracted data into the session profile
    - Persist updated profile and turn history
    - Evaluate intro coverage for phase completion

    Completion rules:
    - coverage reaches threshold, OR
    - number of intro turns reaches max_turns
    """

    phase_name = PhaseType.INTRO
    max_turns = 2
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
        Generate the next intro question.

        We feed the current profile, coverage, and previous turn history
        into the intro question prompt builder through LLMClient.
        """
        coverage = await self.evaluate_coverage(session)

        logger.workflow(
            f"[INTRO] GENERATE_QUESTION "
            f"session={session.session_id}"
        )

        logger.debug(
            f"[INTRO] turn_count="
            f"{len([t for t in session.turns if t.phase == self._phase_label()])}"
        )

        logger.debug(
            f"[INTRO] coverage="
            f"{coverage.model_dump_json(indent=2)}"
        )

        previous_questions, previous_answers = self._get_previous_turn_history(
            session
        )

        result = await self.llm.generate_intro_question(
            IntroQuestionPromptInput(
                candidate_profile=session.candidate_profile,
                coverage=coverage,
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
            f"[INTRO] QUESTION={result.question}"
        )

        session.current_question = result.question

        return result

    async def process_answer(
        self,
        session: InterviewSession,
        answer: str,
    ) -> None:
        """
        Process the candidate's intro answer.

        This:
        - extracts structured intro context
        - merges it into the session profile
        - persists the updated profile
        - records a completed turn in session state and the database
        """
        logger.workflow(
            f"[INTRO] PROCESS_ANSWER session={session.session_id}"
        )

        logger.debug(
            f"[INTRO] ANSWER={answer[:500]}"
        )

        extraction = await self.llm.extract_intro(
            IntroExtractionPromptInput(
                answer=answer,
                resume_context=session.resume_context,
                current_profile=session.candidate_profile,
            )
        )

        logger.debug(
            "[INTRO] EXTRACTION=\n"
            + extraction.model_dump_json(
                indent=2,
                exclude_none=True,
            )
        )

        merged_profile = self._merge_candidate_profile(
            session.candidate_profile,
            extraction,
        )

        session.candidate_profile = merged_profile

        logger.workflow(
            "[INTRO] PROFILE_UPDATED "
            f"role={merged_profile.most_recent_role!r} "
            f"education={merged_profile.education!r}"
        )

        logger.debug(
            "[INTRO] PROFILE_AFTER_MERGE=\n"
            + merged_profile.model_dump_json(
                indent=2,
                exclude_none=True,
            )
        )

        # Persist the merged profile so future requests can reload it.
        logger.database(
            f"[INTRO] UPSERT_PROFILE "
            f"session={session.session_id}"
        )

        ProfileRepository.upsert(
            session.session_id,
            merged_profile.model_dump(),
        )

        question = self._resolve_current_question(session)
        # turn_number = len(
        #     [
        #         turn
        #         for turn in session.turns
        #         if turn.phase == self._phase_label()
        #     ]
        # ) + 1
        turn_number = self._next_turn_number(session)
        phase_label = self._phase_label()

        # We do not have a dedicated intro turn scorer wired in yet,
        # so we store a neutral placeholder assessment for now.
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
            f"[INTRO] TURN_ADDED "
            f"turn={turn_number}"
        )

        logger.database(
            f"[INTRO] INSERT_TURN "
            f"turn={turn_number}"
        )

        # Persist the turn record for replay / analytics.
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

        # Clear the pending question after the answer is recorded.
        session.current_question = None
        logger.workflow(
            "[INTRO] PROCESS_ANSWER_DONE"
        )

    async def evaluate_coverage(
        self,
        session: InterviewSession,
    ) -> CoverageResult:
        coverage = IntroCoverage()
        profile = session.candidate_profile

        coverage.most_recent_role = profile.most_recent_role is not None
        coverage.education = profile.education is not None
        coverage.highlighted_experiences = len(
            profile.highlighted_experiences
        ) > 0
        coverage.domain_keywords = len(profile.domain_keywords) > 0
        coverage.other_context = len(profile.other_context) > 0

        result = CoverageEvaluator.evaluate_intro(
            coverage,
            self.coverage_threshold,
        )

        logger.debug(
            "[INTRO] COVERAGE_RESULT=\n"
            + result.model_dump_json(indent=2)
        )

        logger.workflow(
            f"[INTRO] COVERAGE_SCORE="
            f"{result.score:.2f}"
        )

        return result

    async def is_complete(
        self,
        session: InterviewSession,
    ) -> bool:
        """
        End intro phase when either:
        - coverage reaches threshold, or
        - intro turn count reaches max_turns
        """
        coverage = await self.evaluate_coverage(session)

        logger.workflow(
            f"[INTRO] CHECK_COMPLETE "
            f"coverage={coverage.score:.2f}"
        )

        intro_turn_count = len(
            [
                turn
                for turn in session.turns
                if turn.phase == self._phase_label()
            ]
        )

        complete = (
                coverage.complete
                or intro_turn_count >= self.max_turns
        )

        logger.workflow(
            f"[INTRO] COMPLETE={complete}"
        )

        return complete

    def _merge_candidate_profile(
        self,
        current_profile: CandidateProfile,
        extracted: IntroExtractionResult,
    ) -> CandidateProfile:
        """
        Merge extracted intro data into the current profile.

        Rules:
        - Prefer newly extracted scalar values when present.
        - Preserve existing values when the extractor returns null.
        - Merge list fields without duplicating entries.
        """
        merged_experiences = list(current_profile.highlighted_experiences)
        seen_experiences = {
            self._experience_key(exp)
            for exp in merged_experiences
        }

        for experience in extracted.highlighted_experiences:
            key = self._experience_key(experience)
            if key not in seen_experiences:
                merged_experiences.append(experience)
                seen_experiences.add(key)

        merged_keywords = self._merge_unique_strings(
            current_profile.domain_keywords,
            extracted.domain_keywords,
        )

        merged_other_context = self._merge_unique_strings(
            current_profile.other_context,
            extracted.other_context,
        )

        return current_profile.model_copy(
            update={
                "most_recent_role": (
                    extracted.most_recent_role
                    or current_profile.most_recent_role
                ),
                "education": (
                    extracted.education
                    or current_profile.education
                ),
                "highlighted_experiences": merged_experiences,
                "domain_keywords": merged_keywords,
                "other_context": merged_other_context,
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
        3. A safe fallback for the very first intro answer
        """
        if session.current_question:
            return session.current_question

        if session.turns:
            return session.turns[-1].question

        return "Please introduce yourself."

    def _get_previous_turn_history(
        self,
        session: InterviewSession,
    ) -> tuple[list[str], list[str]]:
        """
        Extract previous intro questions and answers from session turns.
        """
        intro_turns = [
            turn
            for turn in session.turns
            if turn.phase == self.phase_name
        ]

        previous_questions = [
            turn.question
            for turn in intro_turns
        ]

        previous_answers = [
            turn.answer
            for turn in intro_turns
        ]

        return previous_questions, previous_answers

    def _phase_label(self) -> str:
        """
        Convert the phase identifier into a plain string label.

        This keeps stored turn data and prompt metadata stable even
        if PhaseType is implemented as an Enum.
        """
        return getattr(self.phase_name, "value", self.phase_name)

    @staticmethod
    def _merge_unique_strings(
        first: list[str],
        second: list[str],
    ) -> list[str]:
        """
        Merge two string lists while preserving order and removing duplicates.
        """
        merged: list[str] = []
        seen: set[str] = set()

        for value in first + second:
            if value and value not in seen:
                merged.append(value)
                seen.add(value)

        return merged

    @staticmethod
    def _experience_key(experience) -> tuple:
        """
        Build a stable identity key for highlighted experiences.

        This avoids duplicate entries when the extractor returns
        overlapping or repeated experiences.
        """
        return (
            getattr(experience, "organization", None),
            getattr(experience, "timeframe", None),
            getattr(experience, "summary", None),
            tuple(getattr(experience, "responsibilities", []) or []),
            tuple(getattr(experience, "achievements", []) or []),
        )