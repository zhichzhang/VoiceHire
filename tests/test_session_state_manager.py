from datetime import datetime, timedelta, timezone

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.sessions.session_state_manager import (
    SessionStateManager,
)
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.session import InterviewSession


def build_session() -> InterviewSession:
    return InterviewSession(
        session_id="test-session",
        current_phase=PhaseType.INTRO,
        status="active",
        current_question=None,
        current_answer=None,
        turns=[],
        candidate_profile=CandidateProfile(),
        experience_evidence=ExperienceEvidence(),
        evaluation=None,
        resume_context=None,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=7),
    )


def test_next_phase_intro():
    assert (
        SessionStateManager.next_phase(
            PhaseType.INTRO
        )
        == PhaseType.EXPERIENCE
    )


def test_next_phase_experience():
    assert (
        SessionStateManager.next_phase(
            PhaseType.EXPERIENCE
        )
        == PhaseType.EVALUATION
    )


def test_next_phase_evaluation():
    assert (
        SessionStateManager.next_phase(
            PhaseType.EVALUATION
        )
        == PhaseType.COMPLETED
    )


def test_is_active():
    session = build_session()

    assert (
        SessionStateManager.is_active(session)
        is True
    )


def test_is_expired():
    session = build_session()

    session.expires_at = (
        datetime.now(timezone.utc)
        - timedelta(days=1)
    )

    assert (
        SessionStateManager.is_expired(session)
        is True
    )


def test_pending_question():
    session = build_session()

    SessionStateManager.set_pending_question(
        session,
        "Tell me about yourself."
    )

    assert (
        SessionStateManager.has_pending_question(session)
        is True
    )


def test_pending_answer():
    session = build_session()

    SessionStateManager.set_pending_answer(
        session,
        "I am a software engineer."
    )

    assert (
        SessionStateManager.has_pending_answer(session)
        is True
    )


def test_resume_same_question():
    session = build_session()

    SessionStateManager.set_pending_question(
        session,
        "Tell me about yourself."
    )

    assert (
        SessionStateManager.should_resume_same_question(
            session
        )
        is True
    )


def test_advance_phase():
    session = build_session()

    SessionStateManager.advance_phase(session)

    assert (
        session.current_phase
        == PhaseType.EXPERIENCE
    )


def test_mark_completed():
    session = build_session()

    SessionStateManager.set_pending_question(
        session,
        "Question"
    )

    SessionStateManager.set_pending_answer(
        session,
        "Answer"
    )

    SessionStateManager.mark_completed(
        session
    )

    assert (
        session.status
        == "completed"
    )

    assert (
        session.current_phase
        == PhaseType.COMPLETED
    )

    assert session.current_question is None
    assert session.current_answer is None