from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.repositories.session_repository import SessionRepository
from app.server.interview.repositories.turn_repository import TurnRepository
from app.server.interview.sessions.session_loader import LoadedSessionBundle
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.assessment import TurnAssessment
from app.server.models.candidate import CandidateProfile
from app.server.models.evaluation import (
    CommunicationMetrics,
    InterviewEvaluation,
)
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession
from app.server.services.interview_workflow_service import (
    INTRO_FIXED_QUESTION,
    INTRO_FIXED_TIME_LIMIT_SECONDS,
    InterviewWorkflowService,
    WorkflowResult,
)
from app.server.llm.contracts.prompt_outputs import QuestionGenerationResult


class DummyEngine:
    def __init__(self) -> None:
        self.process_answer = AsyncMock()
        self.generate_question = AsyncMock()
        self.finalize = AsyncMock()


@pytest.fixture
def engine() -> DummyEngine:
    return DummyEngine()


@pytest.fixture
def workflow_service(engine: DummyEngine) -> InterviewWorkflowService:
    return InterviewWorkflowService(engine=engine)


@pytest.fixture
def session_repo_spies(monkeypatch):
    update_phase = Mock()
    update_status = Mock()
    update_current_question = Mock()
    update_current_answer = Mock()
    delete = Mock()

    monkeypatch.setattr(SessionRepository, "update_phase", update_phase, raising=False)
    monkeypatch.setattr(SessionRepository, "update_status", update_status, raising=False)
    monkeypatch.setattr(
        SessionRepository,
        "update_current_question",
        update_current_question,
        raising=False,
    )
    monkeypatch.setattr(
        SessionRepository,
        "update_current_answer",
        update_current_answer,
        raising=False,
    )
    monkeypatch.setattr(SessionRepository, "delete", delete, raising=False)

    return {
        "update_phase": update_phase,
        "update_status": update_status,
        "update_current_question": update_current_question,
        "update_current_answer": update_current_answer,
        "delete": delete,
    }


@pytest.fixture
def session() -> InterviewSession:
    now = datetime.now(timezone.utc)

    return InterviewSession(
        session_id="session-001",
        current_phase=PhaseType.INTRO,
        status="active",
        current_question=INTRO_FIXED_QUESTION,
        current_answer=None,
        turns=[],
        candidate_profile=CandidateProfile(),
        experience_evidence=ExperienceEvidence(),
        evaluation=None,
        resume_context=CandidateResume(),
        started_at=now,
        completed_at=None,
        expires_at=now.replace(year=now.year + 1),
    )


def make_bundle(session: InterviewSession) -> LoadedSessionBundle:
    return LoadedSessionBundle(
        candidate={"id": "cand-1", "email": "test@example.com", "name": "Test"},
        resume={"id": "resume-1", "candidate_id": "cand-1"},
        session=session,
    )


def make_question(text: str, phase: str) -> QuestionGenerationResult:
    return QuestionGenerationResult(
        question=text,
        phase=phase,
        target_fields=[],
    )


def make_evaluation() -> InterviewEvaluation:
    return InterviewEvaluation(
        phase_results=[],
        communication_metrics=CommunicationMetrics(
            relevance=0.8,
            clarity=0.7,
            fluency=0.6,
        ),
        communication_score=71.0,
        professional_score=84.0,
        overall_score=80.0,
        assessment_confidence=0.93,
        llm_feedback=None,
    )


def append_placeholder_turn(
    sess: InterviewSession,
    *,
    turn_number: int,
    phase: str,
    question: str,
    answer: str,
) -> None:
    sess.turns.append(
        InterviewTurn(
            turn_number=turn_number,
            phase=phase,
            question=question,
            answer=answer,
            assessment=TurnAssessment(
                relevance=0.0,
                clarity=0.0,
                fluency=0.0,
            ),
        )
    )


@pytest.mark.asyncio
async def test_load_bundle_and_load_session(
    workflow_service: InterviewWorkflowService,
    session: InterviewSession,
    monkeypatch,
) -> None:
    bundle = make_bundle(session)
    load_mock = Mock(return_value=bundle)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        load_mock,
    )

    loaded_bundle = workflow_service.load_bundle("session-001")
    loaded_session = workflow_service.load_session("session-001")

    assert loaded_bundle.session.session_id == "session-001"
    assert loaded_session.session_id == "session-001"
    load_mock.assert_called_with("session-001")


def test_seed_intro_question_sets_fixed_intro_question(
    workflow_service: InterviewWorkflowService,
    session: InterviewSession,
    session_repo_spies,
) -> None:
    session.current_phase = PhaseType.EXPERIENCE
    session.status = "processing"
    session.current_question = None
    session.current_answer = "stale answer"

    result = workflow_service.seed_intro_question(session)

    assert isinstance(result, WorkflowResult)
    assert result.kind == "question"
    assert result.phase == "intro"
    assert result.text == INTRO_FIXED_QUESTION
    assert result.time_limit_seconds == INTRO_FIXED_TIME_LIMIT_SECONDS
    assert result.session is session

    assert session.current_phase == PhaseType.INTRO
    assert session.status == "active"
    assert session.current_question == INTRO_FIXED_QUESTION
    assert session.current_answer is None

    session_repo_spies["update_phase"].assert_called_once_with(
        session.session_id,
        "intro",
    )
    session_repo_spies["update_status"].assert_called_once_with(
        session.session_id,
        "active",
    )
    session_repo_spies["update_current_question"].assert_called_once_with(
        session.session_id,
        INTRO_FIXED_QUESTION,
    )
    session_repo_spies["update_current_answer"].assert_called_once_with(
        session.session_id,
        None,
    )


@pytest.mark.asyncio
async def test_submit_phase_transcript_rejects_terminal_session(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.status = "completed"
    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="I am a software engineer.",
    )

    assert result.kind == "ignored"
    assert result.error == "Session is terminal."
    assert result.session is session
    engine.process_answer.assert_not_awaited()
    engine.generate_question.assert_not_awaited()
    engine.finalize.assert_not_awaited()

    session_repo_spies["update_phase"].assert_not_called()


@pytest.mark.asyncio
async def test_submit_phase_transcript_rejects_phase_mismatch(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.INTRO
    session.current_question = INTRO_FIXED_QUESTION
    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="experience",
        text="I worked on attribution infrastructure.",
    )

    assert result.kind == "error"
    assert result.phase == "intro"
    assert "Phase mismatch" in (result.error or "")
    engine.process_answer.assert_not_awaited()
    engine.generate_question.assert_not_awaited()
    engine.finalize.assert_not_awaited()

    session_repo_spies["update_phase"].assert_not_called()


@pytest.mark.asyncio
async def test_submit_phase_transcript_rejects_empty_text(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.INTRO
    session.current_question = INTRO_FIXED_QUESTION
    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="   ",
    )

    assert result.kind == "ignored"
    assert result.error == "Empty transcript."
    engine.process_answer.assert_not_awaited()
    engine.generate_question.assert_not_awaited()
    engine.finalize.assert_not_awaited()

    session_repo_spies["update_phase"].assert_not_called()


@pytest.mark.asyncio
async def test_submit_phase_transcript_requires_pending_question(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.INTRO
    session.current_question = None
    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="I am a software engineer.",
    )

    assert result.kind == "error"
    assert result.error == "No pending question exists for this session."
    engine.process_answer.assert_not_awaited()
    engine.generate_question.assert_not_awaited()
    engine.finalize.assert_not_awaited()

    session_repo_spies["update_phase"].assert_not_called()


@pytest.mark.asyncio
async def test_submit_phase_transcript_returns_next_question_when_same_phase_continues(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.INTRO
    session.status = "active"
    session.current_question = INTRO_FIXED_QUESTION

    async def process_answer_side_effect(sess: InterviewSession, answer: str) -> None:
        sess.current_answer = answer
        sess.current_question = None
        append_placeholder_turn(
            sess,
            turn_number=1,
            phase="intro",
            question=INTRO_FIXED_QUESTION,
            answer=answer,
        )

    async def generate_question_side_effect(
        sess: InterviewSession,
    ) -> QuestionGenerationResult:
        sess.current_question = "Tell me more about your background."
        return make_question("Tell me more about your background.", "intro")

    engine.process_answer.side_effect = process_answer_side_effect
    engine.generate_question.side_effect = generate_question_side_effect

    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="I am a software engineer.",
    )

    assert result.kind == "question"
    assert result.phase == "intro"
    assert result.text == "Tell me more about your background."
    assert result.session is session

    engine.process_answer.assert_awaited_once()
    engine.generate_question.assert_awaited_once()
    engine.finalize.assert_not_awaited()

    assert session.status == "active"
    assert session.current_question == "Tell me more about your background."
    assert len(session.turns) == 1

    session_repo_spies["update_phase"].assert_called()
    session_repo_spies["update_status"].assert_called()


@pytest.mark.asyncio
async def test_submit_phase_transcript_advancing_to_experience_returns_first_experience_question(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.INTRO
    session.status = "active"
    session.current_question = INTRO_FIXED_QUESTION

    async def process_answer_side_effect(sess: InterviewSession, answer: str) -> None:
        sess.current_answer = answer
        sess.current_question = None
        append_placeholder_turn(
            sess,
            turn_number=1,
            phase="intro",
            question=INTRO_FIXED_QUESTION,
            answer=answer,
        )
        sess.current_phase = PhaseType.EXPERIENCE

    async def generate_question_side_effect(
        sess: InterviewSession,
    ) -> QuestionGenerationResult:
        sess.current_question = "Tell me about one experience from your resume."
        return make_question("Tell me about one experience from your resume.", "experience")

    engine.process_answer.side_effect = process_answer_side_effect
    engine.generate_question.side_effect = generate_question_side_effect

    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="I am a software engineer.",
    )

    assert result.kind == "question"
    assert result.phase == "experience"
    assert result.text == "Tell me about one experience from your resume."
    assert result.session is session

    engine.process_answer.assert_awaited_once()
    engine.generate_question.assert_awaited_once()
    engine.finalize.assert_not_awaited()

    assert session.current_phase == PhaseType.EXPERIENCE
    assert session.current_question == "Tell me about one experience from your resume."
    assert session.status == "active"
    assert len(session.turns) == 1


@pytest.mark.asyncio
async def test_submit_phase_transcript_advancing_to_evaluation_returns_phase_completed(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.EXPERIENCE
    session.status = "active"
    session.current_question = "Tell me about one experience from your resume."

    async def process_answer_side_effect(sess: InterviewSession, answer: str) -> None:
        sess.current_answer = answer
        sess.current_question = None
        append_placeholder_turn(
            sess,
            turn_number=1,
            phase="experience",
            question="Tell me about one experience from your resume.",
            answer=answer,
        )
        sess.current_phase = PhaseType.EVALUATION

    engine.process_answer.side_effect = process_answer_side_effect

    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )

    result = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="experience",
        text="I built attribution infrastructure.",
    )

    assert result.kind == "phase_completed"
    assert result.phase == "evaluation"
    assert result.text == "Interview is ready for final evaluation."
    assert result.session is session

    engine.process_answer.assert_awaited_once()
    engine.generate_question.assert_not_awaited()
    engine.finalize.assert_not_awaited()

    assert session.current_phase == PhaseType.EVALUATION
    assert session.status == "active"
    assert len(session.turns) == 1


@pytest.mark.asyncio
async def test_finalize_generates_report_and_persists_session(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    session.current_phase = PhaseType.EXPERIENCE
    session.status = "active"
    evaluation = make_evaluation()

    async def finalize_side_effect(sess: InterviewSession) -> InterviewEvaluation:
        sess.evaluation = evaluation
        sess.current_phase = PhaseType.COMPLETED
        sess.status = "completed"
        sess.current_question = None
        sess.current_answer = None
        return evaluation

    engine.finalize.side_effect = finalize_side_effect

    bundle = make_bundle(session)
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.TurnRepository.count_incomplete_assessments",
        Mock(return_value=0),
    )

    result = await workflow_service.finalize("session-001")

    assert result.kind == "final_report"
    assert result.phase == "completed"
    assert result.evaluation == evaluation
    assert result.session is session

    engine.finalize.assert_awaited_once_with(session)
    assert session.evaluation == evaluation
    assert session.current_phase == PhaseType.COMPLETED
    assert session.status == "completed"

    session_repo_spies["update_phase"].assert_called()
    session_repo_spies["update_status"].assert_called()


def test_delete_session_delegates_to_repository(
    workflow_service: InterviewWorkflowService,
    session_repo_spies,
) -> None:
    workflow_service.delete_session("session-001")
    session_repo_spies["delete"].assert_called_once_with("session-001")


@pytest.mark.asyncio
async def test_finalize_returns_error_when_turn_assessments_are_still_processing(
    workflow_service: InterviewWorkflowService,
    monkeypatch,
) -> None:
    count_mock = Mock(return_value=1)
    load_mock = Mock()
    persist_mock = Mock()

    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.TurnRepository.count_incomplete_assessments",
        count_mock,
    )
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        load_mock,
    )
    monkeypatch.setattr(
        workflow_service,
        "_persist_session_snapshot",
        persist_mock,
    )

    result = await workflow_service.finalize("session-1")

    assert result.kind == "error"
    assert result.phase == "evaluation"
    assert result.error == "Turn assessments are still processing."

    count_mock.assert_called_once_with("session-1")
    load_mock.assert_not_called()
    workflow_service.engine.finalize.assert_not_awaited()
    persist_mock.assert_not_called()


@pytest.mark.asyncio
async def test_finalize_generates_report_when_turn_assessments_are_complete(
    workflow_service: InterviewWorkflowService,
    session: InterviewSession,
    monkeypatch,
) -> None:
    session.current_phase = PhaseType.EXPERIENCE
    session.status = "active"
    evaluation = make_evaluation()

    bundle = make_bundle(session)
    load_mock = Mock(return_value=bundle)
    persist_mock = Mock()

    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.TurnRepository.count_incomplete_assessments",
        Mock(return_value=0),
    )
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        load_mock,
    )
    monkeypatch.setattr(
        workflow_service,
        "_persist_session_snapshot",
        persist_mock,
    )
    workflow_service.engine.finalize = AsyncMock(return_value=evaluation)

    result = await workflow_service.finalize("session-1")

    assert result.kind == "final_report"
    assert result.phase == "completed"
    assert result.evaluation == evaluation
    assert result.session is session

    assert session.current_phase == PhaseType.EVALUATION
    load_mock.assert_called_once_with("session-1")
    workflow_service.engine.finalize.assert_awaited_once_with(session)
    persist_mock.assert_called_once_with(session)