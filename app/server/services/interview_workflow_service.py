# app/server/services/interview_workflow_service.py

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.engines.interview_engine import InterviewEngine
from app.server.interview.repositories.session_repository import (
    SessionRepository,
)
from app.server.interview.repositories.turn_repository import TurnRepository
from app.server.interview.sessions.session_loader import (
    LoadedSessionBundle,
    SessionLoader,
)
from app.server.interview.sessions.session_state_manager import (
    SessionStateManager,
)
from app.server.models.evaluation import InterviewEvaluation
from app.server.models.session import InterviewSession
from app.server.services.turn_scoring_service import TurnScoringService

PhaseName = Literal["intro", "experience"]

INTRO_FIXED_QUESTION = "Please introduce yourself. You have 90 seconds."
INTRO_FIXED_TIME_LIMIT_SECONDS = 90


class WorkflowResult(BaseModel):
    """
    Unified result returned to API clients after a workflow action.
    """

    kind: Literal[
        "question",
        "phase_completed",
        "final_report",
        "ack",
        "ignored",
        "error",
    ] = Field(
        description="Result type returned to API clients."
    )

    phase: str | None = Field(
        default=None,
        description="Current phase or next phase label.",
    )

    text: str | None = Field(
        default=None,
        description="Question text or user-facing message.",
    )

    time_limit_seconds: int | None = Field(
        default=None,
        description="Time limit for the current question, when applicable.",
    )

    evaluation: InterviewEvaluation | None = Field(
        default=None,
        description="Final interview evaluation.",
    )

    session: InterviewSession | None = Field(
        default=None,
        description="Updated interview session snapshot.",
    )

    error: str | None = Field(
        default=None,
        description="Error message when the workflow cannot continue.",
    )


class InterviewWorkflowService:
    """
    Thin orchestration layer above InterviewEngine.

    Responsibilities:
    - seed the fixed intro question after bootstrap
    - accept phase transcript text from the frontend
    - advance phases when a phase is complete
    - generate the next question when needed
    - finalize the interview only on explicit request
    - persist session state changes
    """

    def __init__(
        self,
        engine: InterviewEngine,
        turn_scoring_service: TurnScoringService | None = None,
    ) -> None:
        self.engine = engine
        self.turn_scoring_service = turn_scoring_service

    def load_bundle(self, session_id: str) -> LoadedSessionBundle:
        return SessionLoader.load(session_id)

    def load_session(self, session_id: str) -> InterviewSession:
        return self.load_bundle(session_id).session

    def seed_intro_question(self, session: InterviewSession) -> WorkflowResult:
        """
        Seed the fixed first intro question into an initialized session.
        """
        session.current_phase = PhaseType.INTRO
        SessionStateManager.mark_active(session)
        session.current_question = INTRO_FIXED_QUESTION
        session.current_answer = None

        self._persist_session_snapshot(session)

        return WorkflowResult(
            kind="question",
            phase="intro",
            text=INTRO_FIXED_QUESTION,
            time_limit_seconds=INTRO_FIXED_TIME_LIMIT_SECONDS,
            session=session,
        )

    async def submit_phase_transcript(
        self,
        session_id: str,
        phase: PhaseName,
        text: str,
    ) -> WorkflowResult:
        """
        Submit a final transcript for the current interactive phase.

        Expected flow:
        - frontend receives final STT text from LiveKit
        - frontend posts text with the current phase
        - workflow engine processes the answer
        - if the phase is incomplete, generate the next question
        - if the phase completes and advances to experience, generate the first
          experience question
        - if the phase completes and advances to evaluation, stop and wait for
          explicit finalize()
        """
        session = self.load_session(session_id)

        if SessionStateManager.is_terminal(session):
            return WorkflowResult(
                kind="ignored",
                phase=self._phase_label(session.current_phase),
                session=session,
                error="Session is terminal.",
            )

        current_phase = self._phase_label(session.current_phase)
        if phase != current_phase:
            return WorkflowResult(
                kind="error",
                phase=current_phase,
                session=session,
                error=f"Phase mismatch: expected {current_phase}, got {phase}.",
            )

        transcript = text.strip()
        if not transcript:
            return WorkflowResult(
                kind="ignored",
                phase=current_phase,
                session=session,
                error="Empty transcript.",
            )

        if not SessionStateManager.has_pending_question(session):
            return WorkflowResult(
                kind="error",
                phase=current_phase,
                session=session,
                error="No pending question exists for this session.",
            )

        SessionStateManager.mark_processing(session)
        self._persist_session_snapshot(session)

        # Capture the phase before processing the answer.
        # process_answer() may advance the session to a new phase.
        previous_phase = PhaseType(
            self._phase_label(session.current_phase)
        )

        await self.engine.process_answer(
            session,
            transcript,
        )

        self._persist_session_snapshot(session)

        if session.turns:
            last_turn = session.turns[-1]
            turn_number = len(session.turns)

            # Schedule turn assessment after the turn is written.
            self._schedule_turn_scoring(
                session=session,
                previous_phase=previous_phase,
                turn_number=turn_number,
                question=last_turn.question,
                answer=last_turn.answer,
            )

        new_phase = session.current_phase

        # Phase completed and advanced to evaluation:
        # stop here and let the frontend call finalize explicitly.
        if new_phase == PhaseType.EVALUATION:
            SessionStateManager.mark_active(session)
            self._persist_session_snapshot(session)

            return WorkflowResult(
                kind="phase_completed",
                phase="evaluation",
                text="Interview is ready for final evaluation.",
                session=session,
            )

        # Phase completed and advanced to the next interactive phase:
        # generate that phase's first question immediately.
        if new_phase != previous_phase:
            next_question = await self.engine.generate_question(session)
            SessionStateManager.mark_active(session)
            self._persist_session_snapshot(session)

            return WorkflowResult(
                kind="question",
                phase=self._phase_label(session.current_phase),
                text=next_question.question,
                session=session,
            )

        # Same phase, more coverage needed:
        next_question = await self.engine.generate_question(session)
        SessionStateManager.mark_active(session)
        self._persist_session_snapshot(session)

        return WorkflowResult(
            kind="question",
            phase=self._phase_label(session.current_phase),
            text=next_question.question,
            session=session,
        )

    async def finalize(
            self,
            session_id: str,
    ) -> WorkflowResult:
        try:
            incomplete_turns = TurnRepository.count_incomplete_assessments(
                session_id
            )
        except Exception as exc:
            return WorkflowResult(
                kind="error",
                phase="evaluation",
                error=f"Unable to verify turn assessment status: {exc}",
            )

        if incomplete_turns > 0:
            return WorkflowResult(
                kind="error",
                phase="evaluation",
                error="Turn assessments are still processing.",
            )

        session = self.load_session(session_id)

        if session.current_phase != PhaseType.EVALUATION:
            session.current_phase = PhaseType.EVALUATION

        evaluation = await self.engine.finalize(session)
        self._persist_session_snapshot(session)

        return WorkflowResult(
            kind="final_report",
            phase="completed",
            evaluation=evaluation,
            session=session,
        )

    def delete_session(self, session_id: str) -> None:
        SessionRepository.delete(session_id)

    def _schedule_turn_scoring(
        self,
        session: InterviewSession,
        previous_phase: PhaseType,
        turn_number: int,
        question: str,
        answer: str,
    ) -> None:
        """
        Fire-and-forget scheduling for turn scoring.

        The turn has already been persisted at this point.
        We enqueue asynchronous communication scoring and
        return immediately so interview flow is not blocked.
        """
        if self.turn_scoring_service is None:
            return

        self.turn_scoring_service.schedule_turn_assessment(
            session_id=session.session_id,
            phase=previous_phase,
            turn_number=turn_number,
            question=question,
            answer=answer,
        )

    def _persist_session_snapshot(self, session: InterviewSession) -> None:
        """
        Persist the mutable session fields that are owned by the workflow layer.
        """
        phase_value = self._phase_label(session.current_phase)

        SessionRepository.update_phase(session.session_id, phase_value)
        SessionRepository.update_status(session.session_id, session.status)
        SessionRepository.update_current_question(
            session.session_id,
            session.current_question,
        )
        SessionRepository.update_current_answer(
            session.session_id,
            session.current_answer,
        )

    @staticmethod
    def _phase_label(phase: str | PhaseType) -> str:
        return getattr(phase, "value", phase)