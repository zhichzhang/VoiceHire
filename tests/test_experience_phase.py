from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.phases.experience_phase import ExperiencePhase
from app.server.llm.contracts.prompt_outputs import (
    ExperienceExtractionResult,
    QuestionGenerationResult,
)
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.assessment import TurnAssessment
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume, ResumeExperience
from app.server.models.session import InterviewSession


class DummyLLM:
    def __init__(self) -> None:
        self.generate_experience_question = AsyncMock()
        self.generate_experience_deep_dive_question = AsyncMock()
        self.extract_experience = AsyncMock()


@pytest.fixture
def mock_llm() -> DummyLLM:
    return DummyLLM()


@pytest.fixture(autouse=True)
def mock_repositories(monkeypatch):
    evidence_upsert_mock = Mock()
    turn_add_mock = Mock()

    monkeypatch.setattr(
        "app.server.interview.phases.experience_phase.EvidenceRepository.upsert",
        evidence_upsert_mock,
    )
    monkeypatch.setattr(
        "app.server.interview.phases.experience_phase.TurnRepository.add_turn",
        turn_add_mock,
    )

    return {
        "evidence_upsert": evidence_upsert_mock,
        "turn_add": turn_add_mock,
    }


@pytest.fixture
def experience_phase(mock_llm: DummyLLM) -> ExperiencePhase:
    return ExperiencePhase(llm=mock_llm)


@pytest.fixture
def session() -> InterviewSession:
    now = datetime.now(timezone.utc)

    return InterviewSession(
        session_id="session-001",
        current_phase=PhaseType.EXPERIENCE,
        status="active",
        current_question=None,
        current_answer=None,
        turns=[],
        candidate_profile=CandidateProfile(),
        experience_evidence=ExperienceEvidence(),
        evaluation=None,
        resume_context=CandidateResume(
            experiences=[
                ResumeExperience(
                    name="Prox Shopping Platform",
                    organization="Prox Shopping",
                    experience_type="internship",
                    summary="Built attribution and redirect systems.",
                )
            ]
        ),
        started_at=now,
        completed_at=None,
        expires_at=now.replace(year=now.year + 1),
    )


@pytest.mark.asyncio
async def test_generate_question_uses_collection_mode_when_no_experience_name(
    experience_phase: ExperiencePhase,
    mock_llm: DummyLLM,
    session: InterviewSession,
) -> None:
    mock_llm.generate_experience_question.return_value = QuestionGenerationResult(
        phase="intro",
        question="Tell me about one experience from your resume.",
        target_fields=["experience_name"],
    )

    result = await experience_phase.generate_question(session)

    assert result.phase == "experience"
    assert result.question == "Tell me about one experience from your resume."
    assert session.current_question == "Tell me about one experience from your resume."

    mock_llm.generate_experience_question.assert_awaited_once()
    mock_llm.generate_experience_deep_dive_question.assert_not_awaited()

    input_data = mock_llm.generate_experience_question.await_args.args[0]
    assert input_data.mode == "collection"
    assert input_data.candidate_profile == session.candidate_profile
    assert input_data.experience_evidence == session.experience_evidence
    assert input_data.coverage.complete is False


@pytest.mark.asyncio
async def test_generate_question_uses_deep_dive_mode_when_experience_name_exists(
    experience_phase: ExperiencePhase,
    mock_llm: DummyLLM,
    session: InterviewSession,
) -> None:
    session.experience_evidence.experience_name = "Prox Shopping"
    session.turns.append(
        InterviewTurn(
            phase="experience",
            question="What did you build?",
            answer="I built attribution infrastructure.",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        )
    )

    mock_llm.generate_experience_deep_dive_question.return_value = QuestionGenerationResult(
        phase="experience",
        question="What was the hardest challenge?",
        target_fields=["challenge"],
    )

    result = await experience_phase.generate_question(session)

    assert result.phase == "experience"
    assert result.question == "What was the hardest challenge?"
    assert session.current_question == "What was the hardest challenge?"

    mock_llm.generate_experience_question.assert_not_awaited()
    mock_llm.generate_experience_deep_dive_question.assert_awaited_once()

    input_data = mock_llm.generate_experience_deep_dive_question.await_args.args[0]
    assert input_data.mode == "deep_dive"
    assert input_data.candidate_profile == session.candidate_profile
    assert input_data.experience_evidence == session.experience_evidence
    assert input_data.dimensions == ["problem_solving", "impact", "ownership", "domain_expertise"]


@pytest.mark.asyncio
async def test_generate_question_rewrites_phase_when_llm_returns_wrong_phase(
    experience_phase: ExperiencePhase,
    mock_llm: DummyLLM,
    session: InterviewSession,
) -> None:
    mock_llm.generate_experience_question.return_value = QuestionGenerationResult(
        phase="intro",
        question="Tell me about a project.",
        target_fields=["experience_name"],
    )

    result = await experience_phase.generate_question(session)

    assert result.phase == "experience"
    assert result.question == "Tell me about a project."


@pytest.mark.asyncio
async def test_process_answer_extracts_merges_persists_and_records_turn(
    experience_phase: ExperiencePhase,
    mock_llm: DummyLLM,
    mock_repositories,
    session: InterviewSession,
) -> None:
    session.current_question = "Tell me about one experience from your resume."

    mock_llm.extract_experience.return_value = ExperienceExtractionResult(
        experience_type="internship",
        experience_name="Prox Shopping",
        what="Built attribution infrastructure",
        why="To improve tracking reliability",
        how="FastAPI, PostgreSQL, Redis",
        challenge="High traffic and consistency",
        outcome="Deterministic attribution and faster debugging",
    )

    await experience_phase.process_answer(
        session,
        "I built attribution infrastructure for Prox Shopping.",
    )

    assert session.current_question is None
    assert session.current_answer is None
    assert session.experience_evidence.experience_type == "internship"
    assert session.experience_evidence.experience_name == "Prox Shopping"
    assert session.experience_evidence.what == "Built attribution infrastructure"
    assert session.experience_evidence.why == "To improve tracking reliability"
    assert session.experience_evidence.how == "FastAPI, PostgreSQL, Redis"
    assert session.experience_evidence.challenge == "High traffic and consistency"
    assert session.experience_evidence.outcome == "Deterministic attribution and faster debugging"

    assert len(session.turns) == 1
    turn = session.turns[0]
    assert turn.phase == "experience"
    assert turn.question == "Tell me about one experience from your resume."
    assert turn.answer == "I built attribution infrastructure for Prox Shopping."
    assert turn.assessment == TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0)

    mock_llm.extract_experience.assert_awaited_once()
    mock_repositories["evidence_upsert"].assert_called_once()
    mock_repositories["turn_add"].assert_called_once()

    input_data = mock_llm.extract_experience.await_args.args[0]
    assert input_data.answer == "I built attribution infrastructure for Prox Shopping."
    assert input_data.candidate_profile == session.candidate_profile
    assert input_data.resume_context == session.resume_context
    assert input_data.experience_context == "Prox Shopping Platform at Prox Shopping"


@pytest.mark.asyncio
async def test_process_answer_preserves_existing_values_when_extraction_returns_nulls(
    experience_phase: ExperiencePhase,
    mock_llm: DummyLLM,
    session: InterviewSession,
) -> None:
    session.current_question = "Tell me about one experience from your resume."
    session.experience_evidence = ExperienceEvidence(
        experience_type="project",
        experience_name="Existing Experience",
        what="Existing what",
        why="Existing why",
        how="Existing how",
        challenge="Existing challenge",
        outcome="Existing outcome",
    )

    mock_llm.extract_experience.return_value = ExperienceExtractionResult(
        experience_type=None,
        experience_name=None,
        what=None,
        why=None,
        how=None,
        challenge=None,
        outcome=None,
    )

    await experience_phase.process_answer(session, "Some answer.")

    assert session.experience_evidence.experience_type == "project"
    assert session.experience_evidence.experience_name == "Existing Experience"
    assert session.experience_evidence.what == "Existing what"
    assert session.experience_evidence.why == "Existing why"
    assert session.experience_evidence.how == "Existing how"
    assert session.experience_evidence.challenge == "Existing challenge"
    assert session.experience_evidence.outcome == "Existing outcome"


@pytest.mark.asyncio
async def test_evaluate_coverage_returns_complete_when_all_fields_present(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.experience_evidence = ExperienceEvidence(
        experience_name="Prox Shopping",
        what="Built attribution infrastructure",
        why="To improve tracking reliability",
        how="FastAPI, PostgreSQL, Redis",
        challenge="High traffic and consistency",
        outcome="Deterministic attribution",
    )

    result = await experience_phase.evaluate_coverage(session)

    assert result.complete is True
    assert result.score == 1.0
    assert result.covered_fields == [
        "experience_name",
        "what",
        "why",
        "how",
        "challenge",
        "outcome",
    ]
    assert result.missing_fields == []


@pytest.mark.asyncio
async def test_evaluate_coverage_returns_incomplete_when_fields_missing(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.experience_evidence.experience_name = "Prox Shopping"
    session.experience_evidence.what = "Built attribution infrastructure"

    result = await experience_phase.evaluate_coverage(session)

    assert result.complete is False
    assert result.score < 0.8
    assert "experience_name" in result.covered_fields
    assert "why" in result.missing_fields
    assert "how" in result.missing_fields
    assert "challenge" in result.missing_fields
    assert "outcome" in result.missing_fields


def test_merge_preserves_existing_values_and_fills_missing_fields(
    experience_phase: ExperiencePhase,
) -> None:
    current = ExperienceEvidence(
        experience_type="internship",
        experience_name="Prox Shopping",
        what="Existing what",
    )

    extracted = ExperienceExtractionResult(
        experience_type=None,
        experience_name=None,
        what=None,
        why="New why",
        how="New how",
        challenge="New challenge",
        outcome="New outcome",
    )

    merged = experience_phase._merge_experience_evidence(current, extracted)

    assert merged.experience_type == "internship"
    assert merged.experience_name == "Prox Shopping"
    assert merged.what == "Existing what"
    assert merged.why == "New why"
    assert merged.how == "New how"
    assert merged.challenge == "New challenge"
    assert merged.outcome == "New outcome"


def test_resolve_current_question_prefers_session_current_question(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.current_question = "Pending question"
    session.turns.append(
        InterviewTurn(
            phase="experience",
            question="Latest question",
            answer="Latest answer",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        )
    )

    assert experience_phase._resolve_current_question(session) == "Pending question"



def test_resolve_current_question_falls_back_to_latest_turn(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.turns.append(
        InterviewTurn(
            phase="experience",
            question="Latest question",
            answer="Latest answer",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        )
    )

    assert experience_phase._resolve_current_question(session) == "Latest question"



def test_resolve_current_question_returns_safe_default_when_no_history(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    assert experience_phase._resolve_current_question(session) == "Tell me about one experience from your resume."



def test_resolve_experience_context_prefers_extracted_experience_name(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.experience_evidence.experience_name = "Prox Shopping"
    session.resume_context = None

    assert experience_phase._resolve_experience_context(session) == "Prox Shopping"



def test_resolve_experience_context_falls_back_to_first_resume_experience(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.experience_evidence.experience_name = None
    session.resume_context = CandidateResume(
        experiences=[
            ResumeExperience(
                name="Fogsight AI Animation",
                organization="Fogsight",
                summary="Production LLM-powered SaaS platform.",
            )
        ]
    )

    assert experience_phase._resolve_experience_context(session) == "Fogsight AI Animation at Fogsight"



def test_get_previous_turn_history_filters_only_experience_turns(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.turns = [
        InterviewTurn(
            phase="intro",
            question="Intro question",
            answer="Intro answer",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        ),
        InterviewTurn(
            phase="experience",
            question="Experience question 1",
            answer="Experience answer 1",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        ),
        InterviewTurn(
            phase="experience",
            question="Experience question 2",
            answer="Experience answer 2",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        ),
    ]

    questions, answers = experience_phase._get_previous_turn_history(session)

    assert questions == ["Experience question 1", "Experience question 2"]
    assert answers == ["Experience answer 1", "Experience answer 2"]



def test_phase_turn_count_counts_only_experience_phase_turns(
    experience_phase: ExperiencePhase,
    session: InterviewSession,
) -> None:
    session.turns = [
        InterviewTurn(
            phase="intro",
            question="Intro question",
            answer="Intro answer",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        ),
        InterviewTurn(
            phase="experience",
            question="Experience question 1",
            answer="Experience answer 1",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        ),
        InterviewTurn(
            phase="experience",
            question="Experience question 2",
            answer="Experience answer 2",
            assessment=TurnAssessment(relevance=0.0, clarity=0.0, fluency=0.0),
        ),
    ]

    assert experience_phase._phase_turn_count(session) == 2


@pytest.mark.parametrize(
    "evidence,expected",
    [
        (
            ExperienceEvidence(),
            ["problem_solving", "impact", "ownership", "domain_expertise"],
        ),
        (
            ExperienceEvidence(
                experience_name="Prox Shopping",
                what="Built attribution infrastructure",
                why="To improve tracking reliability",
            ),
            ["problem_solving", "impact", "domain_expertise"],
        ),
        (
            ExperienceEvidence(
                experience_name="Prox Shopping",
                what="Built attribution infrastructure",
                why="To improve tracking reliability",
                how="FastAPI",
                challenge="Scale",
                outcome="Reliable pipeline",
            ),
            ["problem_solving", "impact", "ownership", "domain_expertise"],
        ),
    ],
)
def test_select_deep_dive_dimensions(
    evidence: ExperienceEvidence,
    expected: list[str],
) -> None:
    assert ExperiencePhase._select_deep_dive_dimensions(evidence) == expected


def test_phase_name_is_experience(experience_phase: ExperiencePhase) -> None:
    assert experience_phase.phase_name == PhaseType.EXPERIENCE
