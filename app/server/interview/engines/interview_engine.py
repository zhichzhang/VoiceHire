# app/server/interview/engines/interview_engine.py

from __future__ import annotations

from typing import Any

from app.server.core.logger import logger
from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.sessions.session_state_manager import (
    SessionStateManager,
)
from app.server.llm.contracts.prompt_outputs import QuestionGenerationResult
from app.server.models.evaluation import InterviewEvaluation
from app.server.models.session import InterviewSession


class InterviewEngine:
    def __init__(
        self,
        intro_phase: Any,
        experience_phase: Any,
        evaluation_engine: Any,
    ):
        self.intro_phase = intro_phase
        self.experience_phase = experience_phase
        self.evaluation_engine = evaluation_engine

    async def start_session(
        self,
        session: InterviewSession,
    ) -> InterviewSession:
        logger.workflow(
            f"[ENGINE] START_SESSION session={session.session_id}"
        )

        SessionStateManager.mark_active(session)
        session.current_phase = PhaseType.INTRO
        session.current_question = None
        session.current_answer = None

        logger.workflow(
            f"[ENGINE] START_SESSION_DONE session={session.session_id} "
            f"phase={session.current_phase}"
        )

        return session

    async def generate_question(
        self,
        session: InterviewSession,
    ) -> QuestionGenerationResult:
        logger.workflow(
            f"[ENGINE] GENERATE_QUESTION "
            f"session={session.session_id} phase={session.current_phase}"
        )

        phase = self._get_phase(session.current_phase)
        result = await phase.generate_question(session)

        logger.workflow(
            f"[ENGINE] GENERATE_QUESTION_DONE "
            f"session={session.session_id} phase={session.current_phase}"
        )

        logger.debug(
            f"[ENGINE] QUESTION={result.question}"
        )

        return result

    async def process_answer(
        self,
        session: InterviewSession,
        answer: str,
    ) -> None:
        logger.workflow(
            f"[ENGINE] PROCESS_ANSWER "
            f"session={session.session_id} phase={session.current_phase}"
        )

        logger.debug(
            f"[ENGINE] ANSWER={answer[:500]}"
        )

        phase = self._get_phase(session.current_phase)

        await phase.process_answer(
            session,
            answer,
        )

        logger.workflow(
            f"[ENGINE] ANSWER_PROCESSED "
            f"session={session.session_id} phase={session.current_phase}"
        )

        if await phase.is_complete(session):
            logger.workflow(
                f"[ENGINE] PHASE_COMPLETE "
                f"session={session.session_id} phase={session.current_phase}"
            )
            await self.advance_phase(session)

    async def advance_phase(
        self,
        session: InterviewSession,
    ) -> InterviewSession:
        logger.workflow(
            f"[ENGINE] ADVANCE_PHASE "
            f"session={session.session_id} current_phase={session.current_phase}"
        )

        next_phase = SessionStateManager.next_phase(
            session.current_phase
        )
        session.current_phase = next_phase

        logger.workflow(
            f"[ENGINE] ADVANCE_PHASE_DONE "
            f"session={session.session_id} next_phase={next_phase}"
        )

        return session

    async def finalize(
            self,
            session: InterviewSession,
    ) -> InterviewEvaluation:
        """
        Finalize the interview by generating the final report,
        attaching it to the session, and marking the session completed.
        """
        logger.workflow(
            f"[ENGINE] FINALIZE_START session={session.session_id}"
        )

        evaluation = await self.evaluation_engine.evaluate(session)
        session.evaluation = evaluation
        SessionStateManager.mark_completed(session)

        logger.success(
            f"[ENGINE] FINALIZE_DONE session={session.session_id}"
        )

        return evaluation

    def _get_phase(
        self,
        phase_type: str,
    ):
        logger.debug(
            f"[ENGINE] _get_phase phase_type={phase_type}"
        )

        if phase_type == PhaseType.INTRO:
            return self.intro_phase

        if phase_type == PhaseType.EXPERIENCE:
            return self.experience_phase

        if phase_type == PhaseType.EVALUATION:
            raise ValueError(
                "Evaluation phase does not support question generation or answer processing. "
                "Use finalize() instead."
            )

        raise ValueError(f"Unknown phase: {phase_type}")