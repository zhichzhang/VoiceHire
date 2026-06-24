from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.engines.interview_engine import InterviewEngine
from app.server.llm.contracts.prompt_outputs import QuestionGenerationResult

from app.server.models.candidate import CandidateProfile
from app.server.models.evaluation import PhaseEvaluation, InterviewEvaluation, CommunicationMetrics
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession


def build_session(
    current_phase: str = PhaseType.INTRO,
    status: str = "active",
) -> InterviewSession:
    now = datetime.now(timezone.utc)

    return InterviewSession(
        session_id="session-001",
        current_phase=current_phase,
        status=status,
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


def build_evaluation() -> InterviewEvaluation:
    return InterviewEvaluation(
        phase_results=[
            PhaseEvaluation(
                phase_name=PhaseType.INTRO,
                dimensions=[],
                overall_score=85.0,
                strengths=["clear intro"],
                improvements=["more impact detail"],
            )
        ],
        communication_metrics=CommunicationMetrics(
            relevance=0.9,
            clarity=0.8,
            fluency=0.7,
        ),
        communication_score=88.0,
        professional_score=84.0,
        overall_score=86.0,
        assessment_confidence=1.0,
        llm_feedback=None,
    )


class DummyPhase:
    def __init__(
        self,
        phase_name: str,
        question_text: str,
        complete_after_answer: bool,
    ):
        self.phase_name = phase_name
        self.question_text = question_text
        self.complete_after_answer = complete_after_answer
        self.generate_calls: list[InterviewSession] = []
        self.process_calls: list[tuple[InterviewSession, str]] = []
        self.is_complete_calls: list[InterviewSession] = []

    async def generate_question(
        self,
        session: InterviewSession,
    ) -> QuestionGenerationResult:
        self.generate_calls.append(session)
        return QuestionGenerationResult(
            question=self.question_text,
            phase=self.phase_name,
            target_fields=["mock_field"],
        )

    async def process_answer(
        self,
        session: InterviewSession,
        answer: str,
    ) -> None:
        self.process_calls.append((session, answer))
        session.current_answer = answer

    async def is_complete(
        self,
        session: InterviewSession,
    ) -> bool:
        self.is_complete_calls.append(session)
        return self.complete_after_answer


class DummyEvaluationEngine:
    def __init__(self, evaluation: InterviewEvaluation):
        self.evaluation = evaluation
        self.calls: list[InterviewSession] = []

    async def evaluate(
        self,
        session: InterviewSession,
    ) -> InterviewEvaluation:
        self.calls.append(session)
        return self.evaluation


@pytest.mark.asyncio
async def test_start_session_sets_intro_and_clears_pending_fields():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=False,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    evaluation_engine = DummyEvaluationEngine(build_evaluation())
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(
        current_phase=PhaseType.EXPERIENCE,
        status="processing",
    )
    session.current_question = "Old question"
    session.current_answer = "Old answer"

    started = await engine.start_session(session)

    assert started is session
    assert session.current_phase == PhaseType.INTRO
    assert session.status == "active"
    assert session.current_question is None
    assert session.current_answer is None


@pytest.mark.asyncio
async def test_generate_question_delegates_to_intro_phase():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=False,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    evaluation_engine = DummyEvaluationEngine(build_evaluation())
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(current_phase=PhaseType.INTRO)

    result = await engine.generate_question(session)

    assert result.question == "Tell me about yourself."
    assert result.phase == PhaseType.INTRO
    assert len(intro_phase.generate_calls) == 1
    assert len(experience_phase.generate_calls) == 0


@pytest.mark.asyncio
async def test_generate_question_delegates_to_experience_phase():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=False,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    evaluation_engine = DummyEvaluationEngine(build_evaluation())
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(current_phase=PhaseType.EXPERIENCE)

    result = await engine.generate_question(session)

    assert result.question == "Tell me about your experience."
    assert result.phase == PhaseType.EXPERIENCE
    assert len(intro_phase.generate_calls) == 0
    assert len(experience_phase.generate_calls) == 1


@pytest.mark.asyncio
async def test_process_answer_advances_when_phase_is_complete():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=True,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    evaluation_engine = DummyEvaluationEngine(build_evaluation())
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(current_phase=PhaseType.INTRO)

    await engine.process_answer(
        session,
        "I am a software engineering intern at Prox Shopping.",
    )

    assert len(intro_phase.process_calls) == 1
    assert intro_phase.process_calls[0][1].startswith(
        "I am a software engineering intern"
    )
    assert session.current_phase == PhaseType.EXPERIENCE


@pytest.mark.asyncio
async def test_process_answer_stays_when_phase_is_not_complete():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=False,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    evaluation_engine = DummyEvaluationEngine(build_evaluation())
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(current_phase=PhaseType.INTRO)

    await engine.process_answer(
        session,
        "I am a software engineering intern at Prox Shopping.",
    )

    assert len(intro_phase.process_calls) == 1
    assert session.current_phase == PhaseType.INTRO


@pytest.mark.asyncio
async def test_finalize_attaches_evaluation_and_marks_completed():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=False,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    expected_evaluation = build_evaluation()
    evaluation_engine = DummyEvaluationEngine(expected_evaluation)
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(current_phase=PhaseType.EVALUATION)
    session.current_question = "pending question"
    session.current_answer = "pending answer"

    evaluation = await engine.finalize(session)

    assert evaluation == expected_evaluation
    assert session.evaluation == expected_evaluation
    assert session.current_phase == PhaseType.COMPLETED
    assert session.status == "completed"
    assert session.current_question is None
    assert session.current_answer is None
    assert len(evaluation_engine.calls) == 1


@pytest.mark.asyncio
async def test_get_phase_unknown_raises():
    intro_phase = DummyPhase(
        phase_name=PhaseType.INTRO,
        question_text="Tell me about yourself.",
        complete_after_answer=False,
    )
    experience_phase = DummyPhase(
        phase_name=PhaseType.EXPERIENCE,
        question_text="Tell me about your experience.",
        complete_after_answer=False,
    )
    evaluation_engine = DummyEvaluationEngine(build_evaluation())
    engine = InterviewEngine(
        intro_phase=intro_phase,
        experience_phase=experience_phase,
        evaluation_engine=evaluation_engine,
    )

    session = build_session(current_phase="unknown")

    with pytest.raises(ValueError, match="Unknown phase"):
        await engine.generate_question(session)