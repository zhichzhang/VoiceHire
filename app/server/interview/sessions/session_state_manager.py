# app/server/interview/engines/session_state_manager.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from app.server.interview.contracts.phase_types import PhaseType
from app.server.models.session import InterviewSession


class SessionStateManager:
    """
    Pure session state helper.

    This class only answers state questions and performs
    phase/status transitions.

    It does NOT know about:
    - HTTP requests
    - cookies
    - database access
    - email
    - resume upload
    - LLM calls
    """

    ACTIVE_STATUSES: Final[set[str]] = {
        "active",
        "processing",
    }

    COMPLETED_STATUSES: Final[set[str]] = {
        "completed",
    }

    TERMINAL_STATUSES: Final[set[str]] = {
        "completed",
        "expired",
        "failed",
        "deleted",
    }

    @staticmethod
    def next_phase(current_phase: str) -> str:
        """
        Return the next phase in the interview lifecycle.
        """
        if current_phase == PhaseType.INTRO:
            return PhaseType.EXPERIENCE

        if current_phase == PhaseType.EXPERIENCE:
            return PhaseType.EVALUATION

        if current_phase == PhaseType.EVALUATION:
            return PhaseType.COMPLETED

        return PhaseType.COMPLETED

    @staticmethod
    def is_completed(session: InterviewSession) -> bool:
        """
        True when the interview is fully completed and the report
        can be shown.
        """
        return (
            session.current_phase == PhaseType.COMPLETED
            or session.status in SessionStateManager.COMPLETED_STATUSES
            or session.evaluation is not None
        )

    @staticmethod
    def is_terminal(session: InterviewSession) -> bool:
        """
        True when the session should no longer continue.
        """
        return session.status in SessionStateManager.TERMINAL_STATUSES

    @staticmethod
    def is_active(session: InterviewSession) -> bool:
        """
        True when the session is still live and can continue.
        """
        return (
            session.status in SessionStateManager.ACTIVE_STATUSES
            and not SessionStateManager.is_expired(session)
        )

    @staticmethod
    def is_expired(session: InterviewSession) -> bool:
        """
        True when the session has passed its expiration timestamp.
        """
        if session.expires_at is None:
            return False

        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        return expires_at <= now

    @staticmethod
    def has_pending_question(session: InterviewSession) -> bool:
        """
        True when the session has a question that has been generated
        but not yet answered.
        """
        return bool(session.current_question)

    @staticmethod
    def has_pending_answer(session: InterviewSession) -> bool:
        """
        True when an answer has been received but not yet fully committed.
        """
        return bool(session.current_answer)

    @staticmethod
    def should_resume_same_question(session: InterviewSession) -> bool:
        """
        True when the next visit should re-open the same pending question.
        """
        return (
            SessionStateManager.has_pending_question(session)
            and session.status in SessionStateManager.ACTIVE_STATUSES
            and not SessionStateManager.is_expired(session)
        )

    @staticmethod
    def should_generate_question(session: InterviewSession) -> bool:
        """
        True when the engine should generate a new question.
        """
        return (
            SessionStateManager.is_active(session)
            and not SessionStateManager.has_pending_question(session)
            and not SessionStateManager.is_completed(session)
        )

    @staticmethod
    def should_accept_answer(session: InterviewSession) -> bool:
        """
        True when the session can accept an answer for the pending question.
        """
        return (
            SessionStateManager.is_active(session)
            and SessionStateManager.has_pending_question(session)
            and not SessionStateManager.has_pending_answer(session)
        )

    @staticmethod
    def can_resume(session: InterviewSession) -> bool:
        """
        True when the session can be resumed from UUID or cookie.
        """
        return (
            not SessionStateManager.is_expired(session)
            and session.status not in {"deleted"}
        )

    @staticmethod
    def mark_processing(session: InterviewSession) -> None:
        """
        Mark a session as currently processing.
        """
        session.status = "processing"

    @staticmethod
    def mark_active(session: InterviewSession) -> None:
        """
        Mark a session as active.
        """
        session.status = "active"

    @staticmethod
    def mark_completed(session: InterviewSession) -> None:
        """
        Mark a session as completed.
        """
        session.status = "completed"
        session.current_question = None
        session.current_answer = None
        session.current_phase = PhaseType.COMPLETED

    @staticmethod
    def mark_failed(session: InterviewSession) -> None:
        """
        Mark a session as failed.
        """
        session.status = "failed"

    @staticmethod
    def clear_pending_question(session: InterviewSession) -> None:
        """
        Clear the pending question after the answer is committed.
        """
        session.current_question = None

    @staticmethod
    def clear_pending_answer(session: InterviewSession) -> None:
        """
        Clear the pending answer after persistence completes.
        """
        session.current_answer = None

    @staticmethod
    def set_pending_question(session: InterviewSession, question: str) -> None:
        """
        Store the current question on the session.
        """
        session.current_question = question

    @staticmethod
    def set_pending_answer(session: InterviewSession, answer: str) -> None:
        """
        Store the current answer on the session.
        """
        session.current_answer = answer

    @staticmethod
    def advance_phase(session: InterviewSession) -> str:
        """
        Advance the session to the next phase and return it.
        """
        session.current_phase = SessionStateManager.next_phase(
            session.current_phase
        )
        return session.current_phase