from datetime import datetime, timezone

import pytest

from app.server.interview.sessions.session_loader import (
    LoadedSessionBundle,
    SessionLoader,
)
from app.server.interview.contracts.phase_types import PhaseType
from app.server.models.candidate import CandidateProfile
from app.server.models.evaluation import InterviewEvaluation
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.Interview_turn import InterviewTurn
from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession


def test_load_missing_session_raises(monkeypatch):
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.SessionRepository.get_by_id",
        lambda session_id: None,
    )

    with pytest.raises(ValueError, match="Session not found"):
        SessionLoader.load("missing-session-id")


def test_load_assembles_full_bundle(monkeypatch):
    session_id = "session-001"
    candidate_id = "candidate-001"

    session_row = {
        "id": session_id,
        "candidate_id": candidate_id,
        "current_phase": PhaseType.EXPERIENCE,
        "status": "active",
        "current_question": "Tell me about your impact.",
        "current_answer": "I improved throughput.",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "expires_at": None,
    }

    candidate_row = {
        "id": candidate_id,
        "email": "zhicheng@example.com",
        "name": "Zhicheng Zhang",
    }

    resume_row = {
        "candidate_id": candidate_id,
        "resume_json": {
            "education": [
                {
                    "institution": "USC",
                    "program": "Computer Science",
                    "timeframe": "2025-01 to 2027-05",
                    "status": "current student",
                }
            ],
            "experiences": [
                {
                    "name": "Software Engineering Intern",
                    "organization": "Prox Shopping",
                    "experience_type": "internship",
                    "timeframe": "2026-01 to 2026-03",
                    "summary": "Built deterministic tracking systems",
                    "skills": ["FastAPI", "PostgreSQL"],
                }
            ],
            "skills": ["backend systems", "distributed systems"],
        },
    }

    profile_row = {
        "session_id": session_id,
        "profile_json": {
            "most_recent_role": "Software Engineer Intern",
            "education": {
                "institution": "USC",
                "program": "Computer Science",
                "status": "current student",
            },
            "highlighted_experiences": [],
            "domain_keywords": ["backend systems"],
            "other_context": ["Loaded from profile repository"],
        },
    }

    evidence_row = {
        "session_id": session_id,
        "evidence_json": {
            "experience_type": "internship",
            "experience_name": "Software Engineering Intern",
            "what": "Built tracking systems",
            "why": "Improve attribution",
            "how": "FastAPI + PostgreSQL",
            "challenge": "Caching",
            "outcome": "Improved reliability",
        },
    }

    evaluation_row = {
        "session_id": session_id,
        "evaluation_json": {
            "phase_results": [],
            "communication_metrics": {
                "relevance": 0.9,
                "clarity": 0.8,
                "fluency": 0.7,
            },
            "communication_score": 88.0,
            "professional_score": 84.0,
            "overall_score": 86.0,
            "assessment_confidence": 1.0,
            "llm_feedback": None,
        },
    }

    turn_rows = [
        {
            "session_id": session_id,
            "turn_number": 1,
            "phase": PhaseType.INTRO,
            "question": "Tell me about yourself.",
            "answer": "I am a CS student at USC.",
            "relevance": 0.9,
            "clarity": 0.8,
            "fluency": 0.7,
        },
        {
            "session_id": session_id,
            "turn_number": 2,
            "phase": PhaseType.EXPERIENCE,
            "question": "Tell me about Prox Shopping.",
            "answer": "I built tracking systems.",
            "relevance": 0.95,
            "clarity": 0.85,
            "fluency": 0.75,
        },
    ]

    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.SessionRepository.get_by_id",
        lambda _session_id: session_row,
    )
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.CandidateRepository.get_by_id",
        lambda _candidate_id: candidate_row,
    )
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.ResumeRepository.get_by_candidate_id",
        lambda _candidate_id: resume_row,
    )
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.ProfileRepository.get_by_session_id",
        lambda _session_id: profile_row,
    )
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.EvidenceRepository.get_by_session_id",
        lambda _session_id: evidence_row,
    )
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.EvaluationRepository.get_by_session_id",
        lambda _session_id: evaluation_row,
    )
    monkeypatch.setattr(
        "app.server.interview.engines.session_loader.TurnRepository.list_by_session_id",
        lambda _session_id: turn_rows,
    )

    bundle = SessionLoader.load(session_id)

    assert isinstance(bundle, LoadedSessionBundle)
    assert bundle.candidate == candidate_row
    assert bundle.resume == resume_row

    session = bundle.session
    assert isinstance(session, InterviewSession)
    assert session.session_id == session_id
    assert session.current_phase == PhaseType.EXPERIENCE
    assert session.status == "active"
    assert session.current_question == "Tell me about your impact."
    assert session.current_answer == "I improved throughput."
    assert isinstance(session.resume_context, CandidateResume)
    assert isinstance(session.candidate_profile, CandidateProfile)
    assert isinstance(session.experience_evidence, ExperienceEvidence)
    assert isinstance(session.evaluation, InterviewEvaluation)

    assert len(session.turns) == 2
    assert isinstance(session.turns[0], InterviewTurn)
    assert session.turns[0].phase == PhaseType.INTRO
    assert session.turns[1].phase == PhaseType.EXPERIENCE

    assert session.evaluation is not None
    assert session.evaluation.communication_score == 88.0
    assert session.evaluation.professional_score == 84.0
    assert session.evaluation.overall_score == 86.0