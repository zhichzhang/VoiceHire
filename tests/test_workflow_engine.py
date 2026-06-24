from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.engines.interview_engine import InterviewEngine

from app.server.models.session import InterviewSession


@pytest.fixture
def session():
    return InterviewSession(
        session_id="session-1",
        current_phase=PhaseType.INTRO,
    )


@pytest.fixture
def intro_phase():
    phase = Mock()
    phase.generate_question = AsyncMock(
        return_value=SimpleNamespace(
            phase=PhaseType.INTRO,
            question="Please introduce yourself.",
            target_fields=[],
        )
    )
    phase.process_answer = AsyncMock()
    phase.is_complete = AsyncMock(return_value=True)
    return phase


@pytest.fixture
def experience_phase():
    phase = Mock()
    phase.generate_question = AsyncMock(
        return_value=SimpleNamespace(
            phase=PhaseType.EXPERIENCE,
            question="Tell me about your most impactful project.",
            target_fields=[],
        )
    )
    phase.process_answer = AsyncMock()
    phase.is_complete = AsyncMock(return_value=True)
    return phase


@pytest.fixture
def evaluation_engine():
    engine = Mock()
    engine.evaluate = AsyncMock(
        return_value=SimpleNamespace(
            overall_score=88.0,
            communication_score=85.0,
            professional_score=90.0,
            assessment_confidence=0.92,
        )
    )
    return engine


@pytest.fixture
def engine(intro_phase, experience_phase, evaluation_engine):
    return InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )


@pytest.mark.asyncio
async def test_start_session_sets_intro(engine, session):
    session.current_phase = PhaseType.EXPERIENCE

    await engine.start_session(session)

    assert session.current_phase == PhaseType.INTRO


@pytest.mark.asyncio
async def test_generate_question_delegates_to_intro_phase(engine, session, intro_phase):
    result = await engine.generate_question(session)

    assert result.question == "Please introduce yourself."
    intro_phase.generate_question.assert_awaited_once_with(session)


@pytest.mark.asyncio
async def test_process_answer_advances_from_intro_to_experience(
    engine,
    session,
    intro_phase,
):
    session.current_phase = PhaseType.INTRO

    await engine.process_answer(session, "I am Zhicheng Zhang.")

    intro_phase.process_answer.assert_awaited_once_with(
        session,
        "I am Zhicheng Zhang.",
    )
    intro_phase.is_complete.assert_awaited_once_with(session)
    assert session.current_phase == PhaseType.EXPERIENCE


@pytest.mark.asyncio
async def test_process_answer_advances_from_experience_to_evaluation(
    engine,
    session,
    experience_phase,
):
    session.current_phase = PhaseType.EXPERIENCE

    await engine.process_answer(session, "I built a tracking system.")

    experience_phase.process_answer.assert_awaited_once_with(
        session,
        "I built a tracking system.",
    )
    experience_phase.is_complete.assert_awaited_once_with(session)
    assert session.current_phase == PhaseType.EVALUATION


@pytest.mark.asyncio
async def test_finalize_saves_evaluation_and_marks_completed(
    engine,
    session,
    evaluation_engine,
):
    session.current_phase = PhaseType.EVALUATION

    evaluation = await engine.finalize(session)

    evaluation_engine.evaluate.assert_awaited_once_with(session)
    assert session.evaluation == evaluation
    assert session.current_phase == PhaseType.COMPLETED