from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.phases.intro_phase import IntroPhase
from app.server.llm.contracts.prompt_outputs import (
    EducationContext,
    HighlightedExperience,
    IntroExtractionResult,
    QuestionGenerationResult,
)
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.assessment import TurnAssessment
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession


def build_session(
    profile: CandidateProfile | None = None,
    turns: list[InterviewTurn] | None = None,
) -> InterviewSession:
    now = datetime.now(timezone.utc)

    return InterviewSession(
        session_id="session-001",
        current_phase=PhaseType.INTRO,
        status="active",
        current_question=None,
        current_answer=None,
        turns=turns or [],
        candidate_profile=profile or CandidateProfile(),
        experience_evidence=ExperienceEvidence(),
        evaluation=None,
        resume_context=CandidateResume(),
        started_at=now,
        completed_at=None,
        expires_at=now.replace(year=now.year + 1),
    )


class DummyLLM:
    def __init__(
        self,
        question_result: QuestionGenerationResult,
        extraction_result: IntroExtractionResult,
    ):
        self.question_result = question_result
        self.extraction_result = extraction_result
        self.question_calls = []
        self.extraction_calls = []

    async def generate_intro_question(self, input_data):
        self.question_calls.append(input_data)
        return self.question_result

    async def extract_intro(self, input_data):
        self.extraction_calls.append(input_data)
        return self.extraction_result


@pytest.mark.asyncio
async def test_generate_question_uses_profile_and_sets_pending_question():
    question_result = QuestionGenerationResult(
        question="Tell me about yourself.",
        phase="intro",
        target_fields=["education"],
    )

    extraction_result = IntroExtractionResult(
        most_recent_role=None,
        education=None,
        highlighted_experiences=[],
        domain_keywords=[],
        other_context=[],
    )

    llm = DummyLLM(
        question_result=question_result,
        extraction_result=extraction_result,
    )

    phase = IntroPhase(llm=llm)
    session = build_session()

    result = await phase.generate_question(session)

    assert isinstance(result, QuestionGenerationResult)
    assert result.question == "Tell me about yourself."
    assert result.phase == "intro"
    assert result.target_fields == ["education"]

    assert len(llm.question_calls) == 1
    assert llm.question_calls[0].candidate_profile == session.candidate_profile
    assert llm.question_calls[0].coverage.complete is False
    assert session.current_question == "Tell me about yourself."


@pytest.mark.asyncio
async def test_process_answer_merges_profile_persists_profile_and_records_turn(
    monkeypatch,
):
    question_result = QuestionGenerationResult(
        question="Tell me about yourself.",
        phase="intro",
        target_fields=["education"],
    )

    extraction_result = IntroExtractionResult(
        most_recent_role="Software Engineering Intern",
        education=EducationContext(
            institution="University of Southern California",
            program="Computer Science",
            status="current student",
        ),
        highlighted_experiences=[
            HighlightedExperience(
                organization="Prox Shopping",
                timeframe="2026-01 to 2026-03",
                summary="Built deterministic tracking systems",
                responsibilities=["Designed click tracking"],
                achievements=["Improved attribution accuracy"],
            )
        ],
        domain_keywords=["backend systems", "distributed systems"],
        other_context=["Interested in scalable systems"],
    )

    llm = DummyLLM(
        question_result=question_result,
        extraction_result=extraction_result,
    )

    profile_upserts: list[tuple[str, dict]] = []
    turn_inserts: list[dict] = []

    def fake_profile_upsert(session_id: str, profile_json: dict):
        profile_upserts.append((session_id, profile_json))
        return {"session_id": session_id, "profile_json": profile_json}

    def fake_turn_add_turn(
        session_id: str,
        turn_number: int,
        phase: str,
        question: str,
        answer: str,
        relevance: float | None = None,
        clarity: float | None = None,
        fluency: float | None = None,
    ):
        turn_inserts.append(
            {
                "session_id": session_id,
                "turn_number": turn_number,
                "phase": phase,
                "question": question,
                "answer": answer,
                "relevance": relevance,
                "clarity": clarity,
                "fluency": fluency,
            }
        )
        return None

    monkeypatch.setattr(
        "app.server.interview.phases.intro_phase.ProfileRepository.upsert",
        fake_profile_upsert,
    )
    monkeypatch.setattr(
        "app.server.interview.phases.intro_phase.TurnRepository.add_turn",
        fake_turn_add_turn,
    )

    phase = IntroPhase(llm=llm)
    session = build_session()
    session.current_question = "Tell me about yourself."

    await phase.process_answer(
        session,
        "I am a software engineering intern at Prox Shopping.",
    )

    assert len(llm.extraction_calls) == 1
    assert llm.extraction_calls[0].answer.startswith(
        "I am a software engineering intern"
    )

    assert session.current_question is None
    assert len(session.turns) == 1
    assert session.turns[0].phase == "intro"
    assert session.turns[0].question == "Tell me about yourself."
    assert session.turns[0].answer.startswith(
        "I am a software engineering intern"
    )

    assert session.candidate_profile.most_recent_role == "Software Engineering Intern"
    assert session.candidate_profile.education is not None
    assert session.candidate_profile.education.institution == "University of Southern California"
    assert "backend systems" in session.candidate_profile.domain_keywords
    assert "Interested in scalable systems" in session.candidate_profile.other_context

    assert len(profile_upserts) == 1
    assert profile_upserts[0][0] == session.session_id
    assert len(turn_inserts) == 1
    assert turn_inserts[0]["session_id"] == session.session_id
    assert turn_inserts[0]["turn_number"] == 1
    assert turn_inserts[0]["phase"] == "intro"
    assert turn_inserts[0]["question"] == "Tell me about yourself."


@pytest.mark.asyncio
async def test_is_complete_when_coverage_reaches_threshold():
    question_result = QuestionGenerationResult(
        question="Tell me about yourself.",
        phase="intro",
        target_fields=["education"],
    )

    extraction_result = IntroExtractionResult(
        most_recent_role=None,
        education=None,
        highlighted_experiences=[],
        domain_keywords=[],
        other_context=[],
    )

    llm = DummyLLM(
        question_result=question_result,
        extraction_result=extraction_result,
    )

    phase = IntroPhase(llm=llm)

    profile = CandidateProfile(
        most_recent_role="Software Engineering Intern",
        education=EducationContext(
            institution="University of Southern California",
            program="Computer Science",
            status="current student",
        ),
        highlighted_experiences=[
            HighlightedExperience(
                organization="Prox Shopping",
                timeframe="2026-01 to 2026-03",
                summary="Built deterministic tracking systems",
                responsibilities=[],
                achievements=[],
            )
        ],
        domain_keywords=["backend systems"],
        other_context=["Interested in scalable systems"],
    )

    session = build_session(profile=profile)

    assert await phase.is_complete(session) is True


@pytest.mark.asyncio
async def test_is_complete_when_max_turns_reached_even_if_coverage_incomplete():
    question_result = QuestionGenerationResult(
        question="Tell me about yourself.",
        phase="intro",
        target_fields=["education"],
    )

    extraction_result = IntroExtractionResult(
        most_recent_role=None,
        education=None,
        highlighted_experiences=[],
        domain_keywords=[],
        other_context=[],
    )

    llm = DummyLLM(
        question_result=question_result,
        extraction_result=extraction_result,
    )

    phase = IntroPhase(llm=llm)

    turns = [
        InterviewTurn(
            phase="intro",
            question="Tell me about yourself.",
            answer="I am a student at USC.",
            assessment=TurnAssessment(
                relevance=0.0,
                clarity=0.0,
                fluency=0.0,
            ),
        ),
        InterviewTurn(
            phase="intro",
            question="Can you tell me more about your education?",
            answer="I study CS.",
            assessment=TurnAssessment(
                relevance=0.0,
                clarity=0.0,
                fluency=0.0,
            ),
        ),
    ]

    session = build_session(turns=turns)

    assert await phase.is_complete(session) is True


@pytest.mark.asyncio
async def test_is_not_complete_when_below_threshold_and_below_max_turns():
    question_result = QuestionGenerationResult(
        question="Tell me about yourself.",
        phase="intro",
        target_fields=["education"],
    )

    extraction_result = IntroExtractionResult(
        most_recent_role=None,
        education=None,
        highlighted_experiences=[],
        domain_keywords=[],
        other_context=[],
    )

    llm = DummyLLM(
        question_result=question_result,
        extraction_result=extraction_result,
    )

    phase = IntroPhase(llm=llm)
    session = build_session()

    assert await phase.is_complete(session) is False