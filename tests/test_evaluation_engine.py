from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.contracts.rubics import INTRO_WEIGHTS, EXPERIENCE_WEIGHTS, INTERVIEW_WEIGHTS
from app.server.interview.engines.evaluation_engine import EvaluationEngine
from app.server.llm.contracts.prompt_outputs import (
    DimensionScore as LLMDimensionScore,
    InterviewFeedbackResult,
    PhaseEvaluationResult,
)
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.assessment import TurnAssessment
from app.server.models.candidate import CandidateProfile
from app.server.models.evaluation import (
    CommunicationMetrics,
    DimensionScore as ModelDimensionScore,
    InterviewEvaluation,
    PhaseEvaluation,
)
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.interview_feedback import (
    LLMInterviewFeedback,
    Recommendation,
)
from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession


class DummyLLM:
    def __init__(self) -> None:
        self.evaluate_phase = AsyncMock()
        self.generate_final_evaluation = AsyncMock()


@pytest.fixture
def mock_llm() -> DummyLLM:
    return DummyLLM()


@pytest.fixture(autouse=True)
def mock_evaluation_repository(monkeypatch):
    upsert_mock = Mock()

    monkeypatch.setattr(
        "app.server.interview.engines.evaluation_engine.EvaluationRepository.upsert",
        upsert_mock,
    )

    return upsert_mock


@pytest.fixture
def evaluation_engine(mock_llm: DummyLLM) -> EvaluationEngine:
    return EvaluationEngine(llm=mock_llm)


@pytest.fixture
def session() -> InterviewSession:
    now = datetime.now(timezone.utc)

    return InterviewSession(
        session_id="session-001",
        current_phase=PhaseType.EVALUATION,
        status="active",
        current_question=None,
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


def build_turn(
    relevance: float,
    clarity: float,
    fluency: float,
    phase: str = "experience",
    question: str = "Question",
    answer: str = "Answer",
) -> InterviewTurn:
    return InterviewTurn(
        phase=phase,
        question=question,
        answer=answer,
        assessment=TurnAssessment(
            relevance=relevance,
            clarity=clarity,
            fluency=fluency,
        ),
    )


def build_phase_result(
    phase_name: str,
    overall_score: float,
    dimension_name: str,
    dimension_score: float,
) -> PhaseEvaluationResult:
    return PhaseEvaluationResult(
        phase_name=phase_name,
        dimensions=[
            LLMDimensionScore(
                name=dimension_name,
                score=dimension_score,
                justification=f"Justification for {dimension_name}.",
            )
        ],
        overall_score=overall_score,
        strengths=[f"{phase_name} strength"],
        improvements=[f"{phase_name} improvement"],
    )


def build_feedback_result() -> InterviewFeedbackResult:
    return InterviewFeedbackResult(
        assessment_confidence=0.91,
        llm_feedback=LLMInterviewFeedback(
            summary="Strong performance overall.",
            strengths=[
                "Clear structure",
                "Good ownership",
            ],
            weaknesses=[
                "Could quantify impact more often",
            ],
            recommendations=[
                Recommendation(
                    category="impact",
                    priority="medium",
                    recommendation="Use concrete metrics when describing outcomes.",
                ),
                Recommendation(
                    category="communication",
                    priority="low",
                    recommendation="Keep answers slightly more concise when possible.",
                ),
            ],
        ),
    )


@pytest.mark.asyncio
async def test_evaluate_when_no_turns_returns_zero_communication_metrics(
    evaluation_engine: EvaluationEngine,
    mock_llm: DummyLLM,
    session: InterviewSession,
) -> None:
    mock_llm.evaluate_phase.side_effect = [
        build_phase_result("intro", 72.0, "clarity", 74.0),
        build_phase_result("experience", 84.0, "ownership", 86.0),
    ]
    mock_llm.generate_final_evaluation.return_value = build_feedback_result()

    result = await evaluation_engine.evaluate(session)

    assert isinstance(result, InterviewEvaluation)
    assert result.communication_metrics == CommunicationMetrics(
        relevance=0.0,
        clarity=0.0,
        fluency=0.0,
    )
    assert result.communication_score == 0.0
    assert result.professional_score == pytest.approx(
        72.0 * 0.25 + 84.0 * 0.75
    )
    assert result.overall_score == pytest.approx(
        result.communication_score * 0.3
        + result.professional_score * 0.7
    )
    assert result.assessment_confidence == 0.91
    assert result.llm_feedback.summary == "Strong performance overall."
    assert len(result.phase_results) == 2


@pytest.mark.asyncio
async def test_evaluate_aggregates_communication_and_persists_evaluation(
    evaluation_engine: EvaluationEngine,
    mock_llm: DummyLLM,
    mock_evaluation_repository,
    session: InterviewSession,
) -> None:
    session.turns = [
        build_turn(
            relevance=0.9,
            clarity=0.8,
            fluency=0.7,
            phase="intro",
            question="Introduce yourself.",
            answer="I am a software engineer.",
        ),
        build_turn(
            relevance=0.7,
            clarity=0.6,
            fluency=0.5,
            phase="experience",
            question="Tell me about your project.",
            answer="I built attribution infrastructure.",
        ),
    ]

    mock_llm.evaluate_phase.side_effect = [
        build_phase_result("intro", 80.0, "clarity", 82.0),
        build_phase_result("experience", 90.0, "ownership", 92.0),
    ]
    mock_llm.generate_final_evaluation.return_value = build_feedback_result()

    result = await evaluation_engine.evaluate(session)

    expected_communication_score = (
        0.8 * 0.4 + 0.7 * 0.3 + 0.6 * 0.3
    ) * 100

    assert result.communication_metrics == CommunicationMetrics(
        relevance=0.8,
        clarity=0.7,
        fluency=0.6,
    )
    assert result.communication_score == pytest.approx(
        expected_communication_score
    )
    assert result.professional_score == pytest.approx(
        80.0 * 0.25 + 90.0 * 0.75
    )
    assert result.overall_score == pytest.approx(
        result.communication_score * 0.3
        + result.professional_score * 0.7
    )

    assert result.phase_results[0].phase_name == "intro"
    assert result.phase_results[1].phase_name == "experience"
    assert result.phase_results[0].dimensions[0] == ModelDimensionScore(
        name="clarity",
        score=82.0,
        justification="Justification for clarity.",
    )

    mock_evaluation_repository.assert_called_once()
    saved_session_id, saved_payload = mock_evaluation_repository.call_args.args
    assert saved_session_id == session.session_id
    assert saved_payload["overall_score"] == pytest.approx(
        result.overall_score
    )
    assert saved_payload["assessment_confidence"] == 0.91
    assert saved_payload["llm_feedback"]["summary"] == "Strong performance overall."

    final_context = mock_llm.generate_final_evaluation.await_args.args[0]
    assert final_context["candidate_profile"] == session.candidate_profile
    assert final_context["experience_evidence"] == session.experience_evidence
    assert len(final_context["phase_evaluations"]) == 2
    assert final_context["communication_metrics"] == result.communication_metrics
    assert final_context["interview_evaluation"]["communication_score"] == pytest.approx(
        result.communication_score
    )
    assert final_context["interview_evaluation"]["professional_score"] == pytest.approx(
        result.professional_score
    )
    assert len(final_context["interview_evaluation"]["transcript"]) == 2


@pytest.mark.asyncio
async def test_evaluate_phase_results_uses_rubrics_and_transcript(
    evaluation_engine: EvaluationEngine,
    mock_llm: DummyLLM,
    session: InterviewSession,
) -> None:
    session.turns = [
        build_turn(
            relevance=1.0,
            clarity=0.9,
            fluency=0.8,
            phase="intro",
            question="Tell me about yourself.",
            answer="I am a student.",
        ),
        build_turn(
            relevance=0.8,
            clarity=0.7,
            fluency=0.6,
            phase="experience",
            question="Tell me about your project.",
            answer="I built a pipeline.",
        ),
    ]

    mock_llm.evaluate_phase.side_effect = [
        build_phase_result("intro", 75.0, "relevance", 76.0),
        build_phase_result("experience", 88.0, "ownership", 89.0),
    ]

    communication_metrics = CommunicationMetrics(
        relevance=0.9,
        clarity=0.8,
        fluency=0.7,
    )

    results = await evaluation_engine._evaluate_phase_results(
        session,
        communication_metrics=communication_metrics,
    )

    assert len(results) == 2
    assert results[0].phase_name == "intro"
    assert results[1].phase_name == "experience"

    intro_context = mock_llm.evaluate_phase.await_args_list[0].args[0]
    exp_context = mock_llm.evaluate_phase.await_args_list[1].args[0]

    assert intro_context["rubric"] == {
        getattr(k, "value", str(k)): v for k, v in INTRO_WEIGHTS.items()
    }
    assert exp_context["rubric"] == {
        getattr(k, "value", str(k)): v for k, v in EXPERIENCE_WEIGHTS.items()
    }

    assert intro_context["phase_name"] == "intro"
    assert exp_context["phase_name"] == "experience"
    assert len(intro_context["dimensions"]) > 0
    assert len(exp_context["dimensions"]) > 0


def test_score_communication(
    evaluation_engine: EvaluationEngine,
) -> None:
    metrics = CommunicationMetrics(
        relevance=0.8,
        clarity=0.7,
        fluency=0.6,
    )

    score = evaluation_engine._score_communication(metrics)

    expected = (0.8 * 0.4 + 0.7 * 0.3 + 0.6 * 0.3) * 100
    assert score == pytest.approx(expected)


def test_score_professional_uses_interview_weights(
    evaluation_engine: EvaluationEngine,
) -> None:
    phase_results = [
        PhaseEvaluation(
            phase_name="intro",
            dimensions=[],
            overall_score=80.0,
            strengths=[],
            improvements=[],
        ),
        PhaseEvaluation(
            phase_name="experience",
            dimensions=[],
            overall_score=90.0,
            strengths=[],
            improvements=[],
        ),
    ]

    score = evaluation_engine._score_professional(phase_results)

    expected = (
        80.0 * INTERVIEW_WEIGHTS["intro"]
        + 90.0 * INTERVIEW_WEIGHTS["experience"]
    )
    assert score == pytest.approx(expected)


def test_score_professional_renormalizes_when_one_phase_missing(
    evaluation_engine: EvaluationEngine,
) -> None:
    phase_results = [
        PhaseEvaluation(
            phase_name="experience",
            dimensions=[],
            overall_score=88.0,
            strengths=[],
            improvements=[],
        ),
    ]

    score = evaluation_engine._score_professional(phase_results)

    assert score == pytest.approx(88.0)


def test_get_rubric_for_phase(
    evaluation_engine: EvaluationEngine,
) -> None:
    assert evaluation_engine._get_rubric_for_phase("intro") == INTRO_WEIGHTS
    assert evaluation_engine._get_rubric_for_phase("experience") == EXPERIENCE_WEIGHTS
    assert evaluation_engine._get_rubric_for_phase("other") == {}


def test_rubric_to_payload(
    evaluation_engine: EvaluationEngine,
) -> None:
    payload = evaluation_engine._rubric_to_payload(INTRO_WEIGHTS)

    assert "relevance" in payload
    assert "clarity" in payload
    assert "fluency" in payload
    assert all(isinstance(k, str) for k in payload.keys())


def test_dimension_specs(
    evaluation_engine: EvaluationEngine,
) -> None:
    specs = evaluation_engine._dimension_specs(EXPERIENCE_WEIGHTS)

    assert len(specs) == len(EXPERIENCE_WEIGHTS)
    assert all("name" in item and "weight" in item for item in specs)
    weights = [item["weight"] for item in specs]
    assert weights == sorted(weights, reverse=True)