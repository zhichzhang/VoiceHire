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
async def test_full_interview_flow(
    workflow_service: InterviewWorkflowService,
    engine: DummyEngine,
    monkeypatch,
    session_repo_spies,
    session: InterviewSession,
) -> None:
    """
    Smoke test for the full interview path:

    seed intro -> intro answer -> intro follow-up -> experience answer
    -> experience follow-up -> experience answer -> final evaluation
    """
    evaluation = make_evaluation()
    bundle = make_bundle(session)

    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.SessionLoader.load",
        Mock(return_value=bundle),
    )
    monkeypatch.setattr(
        "app.server.services.interview_workflow_service.TurnRepository.count_incomplete_assessments",
        Mock(return_value=0),
    )

    async def process_answer_side_effect(
        sess: InterviewSession,
        answer: str,
    ) -> None:
        if sess.current_phase == PhaseType.INTRO:
            intro_turn_count = sum(
                1 for turn in sess.turns if turn.phase == "intro"
            )
            question = sess.current_question or INTRO_FIXED_QUESTION

            sess.current_answer = answer
            sess.current_question = None

            append_placeholder_turn(
                sess,
                turn_number=intro_turn_count + 1,
                phase="intro",
                question=question,
                answer=answer,
            )

            if intro_turn_count + 1 >= 2:
                sess.current_phase = PhaseType.EXPERIENCE

            return

        if sess.current_phase == PhaseType.EXPERIENCE:
            experience_turn_count = sum(
                1 for turn in sess.turns if turn.phase == "experience"
            )
            question = (
                sess.current_question
                or "Tell me about one experience from your resume."
            )

            sess.current_answer = answer
            sess.current_question = None

            append_placeholder_turn(
                sess,
                turn_number=experience_turn_count + 1,
                phase="experience",
                question=question,
                answer=answer,
            )

            if experience_turn_count + 1 >= 2:
                sess.current_phase = PhaseType.EVALUATION

            return

        raise AssertionError(f"Unexpected phase: {sess.current_phase}")

    async def generate_question_side_effect(
        sess: InterviewSession,
    ) -> QuestionGenerationResult:
        if sess.current_phase == PhaseType.INTRO:
            question = "Tell me more about your background."
            sess.current_question = question
            return make_question(question, "intro")

        if sess.current_phase == PhaseType.EXPERIENCE:
            experience_turn_count = sum(
                1 for turn in sess.turns if turn.phase == "experience"
            )
            if experience_turn_count == 0:
                question = "Tell me about one experience from your resume."
            else:
                question = "What was the hardest challenge you faced?"

            sess.current_question = question
            return make_question(question, "experience")

        raise AssertionError(
            f"generate_question() should not be called in phase: {sess.current_phase}"
        )

    async def finalize_side_effect(
        sess: InterviewSession,
    ) -> InterviewEvaluation:
        sess.evaluation = evaluation
        sess.current_phase = PhaseType.COMPLETED
        sess.status = "completed"
        sess.current_question = None
        sess.current_answer = None
        return evaluation

    engine.process_answer.side_effect = process_answer_side_effect
    engine.generate_question.side_effect = generate_question_side_effect
    engine.finalize.side_effect = finalize_side_effect

    seed_result = workflow_service.seed_intro_question(session)
    assert seed_result.kind == "question"
    assert seed_result.phase == "intro"
    assert seed_result.text == INTRO_FIXED_QUESTION
    assert seed_result.time_limit_seconds == INTRO_FIXED_TIME_LIMIT_SECONDS
    assert session.current_phase == PhaseType.INTRO
    assert session.current_question == INTRO_FIXED_QUESTION
    assert session.status == "active"

    r1 = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="I am a software engineer.",
    )
    assert r1.kind == "question"
    assert r1.phase == "intro"
    assert r1.text == "Tell me more about your background."
    assert session.current_phase == PhaseType.INTRO
    assert len(session.turns) == 1

    r2 = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="intro",
        text="I built backend systems and worked on distributed infrastructure.",
    )
    assert r2.kind == "question"
    assert r2.phase == "experience"
    assert r2.text == "Tell me about one experience from your resume."
    assert session.current_phase == PhaseType.EXPERIENCE
    assert len(session.turns) == 2

    r3 = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="experience",
        text="I designed an attribution pipeline.",
    )
    assert r3.kind == "question"
    assert r3.phase == "experience"
    assert r3.text == "What was the hardest challenge you faced?"
    assert session.current_phase == PhaseType.EXPERIENCE
    assert len(session.turns) == 3

    r4 = await workflow_service.submit_phase_transcript(
        session_id="session-001",
        phase="experience",
        text="The hardest part was keeping the pipeline deterministic at scale.",
    )
    assert r4.kind == "phase_completed"
    assert r4.phase == "evaluation"
    assert r4.text == "Interview is ready for final evaluation."
    assert session.current_phase == PhaseType.EVALUATION
    assert len(session.turns) == 4

    final_result = await workflow_service.finalize("session-001")
    assert final_result.kind == "final_report"
    assert final_result.phase == "completed"
    assert final_result.evaluation == evaluation
    assert final_result.session is session

    assert session.status == "completed"
    assert session.current_phase == PhaseType.COMPLETED
    assert session.evaluation == evaluation

    assert [turn.phase for turn in session.turns] == [
        "intro",
        "intro",
        "experience",
        "experience",
    ]

    session_repo_spies["update_phase"].assert_called()
    session_repo_spies["update_status"].assert_called()
    engine.process_answer.assert_awaited()
    engine.generate_question.assert_awaited()
    engine.finalize.assert_awaited_once_with(session)