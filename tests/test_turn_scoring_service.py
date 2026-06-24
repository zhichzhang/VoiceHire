from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.models.assessment import TurnAssessment
from app.server.services.turn_scoring_service import TurnScoringService


@pytest.fixture
def mock_phase() -> Mock:
    phase = Mock()
    phase.assess_turn = AsyncMock(
        return_value=TurnAssessment(
            relevance=0.8,
            clarity=0.9,
            fluency=0.7,
        )
    )
    return phase


@pytest.fixture
def scoring_service(mock_phase: Mock) -> TurnScoringService:
    return TurnScoringService(
        phases={
            PhaseType.INTRO: mock_phase,
        }
    )


@pytest.mark.asyncio
async def test_score_and_persist_turn_success(
    scoring_service: TurnScoringService,
    mock_phase: Mock,
    monkeypatch,
) -> None:
    session = Mock()

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.SessionLoader.load",
        Mock(
            return_value=Mock(
                session=session,
            )
        ),
    )

    mark_processing = Mock()
    update_assessment = Mock()

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.TurnRepository.mark_assessment_processing",
        mark_processing,
    )

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.TurnRepository.update_assessment",
        update_assessment,
    )

    await scoring_service.score_and_persist_turn(
        session_id="session-1",
        phase=PhaseType.INTRO,
        turn_number=1,
        question="Tell me about yourself",
        answer="I am a software engineer",
    )

    mark_processing.assert_called_once_with(
        session_id="session-1",
        turn_number=1,
    )

    mock_phase.assess_turn.assert_awaited_once_with(
        session=session,
        question="Tell me about yourself",
        answer="I am a software engineer",
    )

    update_assessment.assert_called_once_with(
        session_id="session-1",
        turn_number=1,
        relevance=0.8,
        clarity=0.9,
        fluency=0.7,
    )


@pytest.mark.asyncio
async def test_score_and_persist_turn_unsupported_phase(
    scoring_service: TurnScoringService,
    monkeypatch,
) -> None:
    mark_failed = Mock()

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.TurnRepository.mark_assessment_failed",
        mark_failed,
    )

    await scoring_service.score_and_persist_turn(
        session_id="session-1",
        phase=PhaseType.EXPERIENCE,
        turn_number=1,
        question="Question",
        answer="Answer",
    )

    mark_failed.assert_called_once()

    kwargs = mark_failed.call_args.kwargs
    assert kwargs["session_id"] == "session-1"
    assert kwargs["turn_number"] == 1
    assert "Unsupported phase" in kwargs["error"]


@pytest.mark.asyncio
async def test_score_and_persist_turn_scoring_failure(
    scoring_service: TurnScoringService,
    mock_phase: Mock,
    monkeypatch,
) -> None:
    session = Mock()

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.SessionLoader.load",
        Mock(
            return_value=Mock(
                session=session,
            )
        ),
    )

    mock_phase.assess_turn.side_effect = RuntimeError("LLM timeout")

    mark_processing = Mock()
    mark_failed = Mock()

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.TurnRepository.mark_assessment_processing",
        mark_processing,
    )

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.TurnRepository.mark_assessment_failed",
        mark_failed,
    )

    await scoring_service.score_and_persist_turn(
        session_id="session-1",
        phase=PhaseType.INTRO,
        turn_number=1,
        question="Question",
        answer="Answer",
    )

    mark_processing.assert_called_once_with(
        session_id="session-1",
        turn_number=1,
    )

    mock_phase.assess_turn.assert_awaited_once_with(
        session=session,
        question="Question",
        answer="Answer",
    )

    mark_failed.assert_called_once()

    kwargs = mark_failed.call_args.kwargs
    assert kwargs["session_id"] == "session-1"
    assert kwargs["turn_number"] == 1
    assert "LLM timeout" in kwargs["error"]


def test_schedule_turn_assessment(
    scoring_service: TurnScoringService,
    monkeypatch,
) -> None:
    mock_task = Mock(name="task")

    def fake_create_task(coro):
        coro.close()
        return mock_task

    monkeypatch.setattr(
        "app.server.services.turn_scoring_service.asyncio.create_task",
        fake_create_task,
    )

    task = scoring_service.schedule_turn_assessment(
        session_id="session-1",
        phase=PhaseType.INTRO,
        turn_number=1,
        question="Question",
        answer="Answer",
    )

    assert task is mock_task