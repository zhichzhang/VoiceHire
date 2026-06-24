from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.server.interview.sessions.session_initializer import (
    SessionBootstrapResult,
)
from app.server.services import (
    ApplicationBootstrapService,
)
from app.server.models.application_bootstrap import (
    ResumePreflightResult,
    ResumeUpsertDecision,
)
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume
from app.server.models.session import InterviewSession


SEED_RESUME_TEXT = """
ZHICHENG ZHANG
Los Angeles, CA
zzhang32@usc.edu
zhichzhang.dev
github.com/zhichzhang
linkedin.com/in/zhichzhang

EDUCATION
University of Southern California
Master of Science in Computer Science
Expected May 2027

China University of Mining and Technology
Bachelor of Engineering in Electronic Information Science and Technology
Sep 2017 – Jun 2021

EXPERIENCE
Prox Shopping
Software Engineering Intern
Jan 2026 – Mar 2026

Fogsight
Software Engineering Intern
May 2025 – Aug 2025

SKILLS
Python, TypeScript, Java, C++, PostgreSQL, Kafka, Redis, Docker, AWS
""".strip()


def build_session(
    session_id: str = "session-001",
) -> InterviewSession:
    now = datetime.now(timezone.utc)

    return InterviewSession(
        session_id=session_id,
        current_phase="intro",
        status="active",
        current_question=None,
        current_answer=None,
        turns=[],
        candidate_profile=CandidateProfile(),
        experience_evidence=ExperienceEvidence(),
        evaluation=None,
        resume_context=None,
        started_at=now,
        completed_at=None,
        expires_at=now + timedelta(days=7),
    )


class DummyLLM:
    def __init__(self, normalized_resume: CandidateResume):
        self.normalized_resume = normalized_resume
        self.calls: list[dict[str, object]] = []

    async def normalize_resume(self, input_data):
        self.calls.append(
            {
                "raw_resume_text": input_data.raw_resume_text,
                "name": input_data.name,
                "email": input_data.email,
                "current_resume_context": input_data.current_resume_context,
            }
        )
        return self.normalized_resume


@pytest.mark.asyncio
async def test_bootstrap_with_valid_resume_normalizes_and_upserts(monkeypatch):
    existing_candidate = {
        "id": "candidate-001",
        "email": "zzhang32@usc.edu",
        "name": "Old Name",
    }

    existing_resume_row = {
        "candidate_id": "candidate-001",
        "resume_json": {
            "education": [
                {
                    "institution": "Old University",
                    "program": "Old Program",
                    "timeframe": "2020-2022",
                    "status": "graduated",
                }
            ],
            "experiences": [],
            "skills": ["old-skill"],
        },
    }

    normalized_resume = CandidateResume.model_validate(
        {
            "education": [
                {
                    "institution": "University of Southern California",
                    "program": "Master of Science in Computer Science",
                    "timeframe": "2025-2027",
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
            "skills": ["Python", "TypeScript", "PostgreSQL"],
        }
    )

    candidate_upsert_row = {
        "id": "candidate-001",
        "email": "zzhang32@usc.edu",
        "name": "Zhicheng Zhang",
    }

    resume_upsert_row = {
        "candidate_id": "candidate-001",
        "resume_json": normalized_resume.model_dump(),
    }

    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.get_by_email",
        lambda email: existing_candidate,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.get_by_candidate_id",
        lambda candidate_id: existing_resume_row,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.upsert",
        lambda candidate_id, email, name: candidate_upsert_row,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.upsert",
        lambda candidate_id, resume_json: resume_upsert_row,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.SessionInitializer.initialize",
        lambda email: SessionBootstrapResult(
            candidate=candidate_upsert_row,
            resume=resume_upsert_row,
            session=build_session(),
        ),
    )

    llm = DummyLLM(normalized_resume=normalized_resume)

    result = await ApplicationBootstrapService.bootstrap(
        email="zzhang32@usc.edu",
        name="Zhicheng Zhang",
        raw_resume_text=SEED_RESUME_TEXT,
        llm=llm,
    )

    assert result.is_new_candidate is False
    assert result.resume_updated is True
    assert result.used_existing_resume is False
    assert result.candidate == candidate_upsert_row
    assert result.resume == resume_upsert_row
    assert result.normalized_resume == normalized_resume
    assert result.session.session_id == "session-001"

    assert len(llm.calls) == 1
    assert llm.calls[0]["email"] == "zzhang32@usc.edu"
    assert llm.calls[0]["name"] == "Zhicheng Zhang"
    assert llm.calls[0]["current_resume_context"] is not None


@pytest.mark.asyncio
async def test_bootstrap_empty_resume_uses_existing_resume(monkeypatch):
    existing_candidate = {
        "id": "candidate-001",
        "email": "zzhang32@usc.edu",
        "name": "Zhicheng Zhang",
    }

    existing_resume_row = {
        "candidate_id": "candidate-001",
        "resume_json": {
            "education": [
                {
                    "institution": "University of Southern California",
                    "program": "Master of Science in Computer Science",
                    "timeframe": "2025-2027",
                    "status": "current student",
                }
            ],
            "experiences": [],
            "skills": ["Python", "TypeScript"],
        },
    }

    candidate_upsert_row = {
        "id": "candidate-001",
        "email": "zzhang32@usc.edu",
        "name": "Zhicheng Zhang",
    }

    candidate_upsert_called = {"value": False}
    resume_upsert_called = {"value": False}
    llm_called = {"value": False}

    def candidate_upsert(candidate_id, email, name):
        candidate_upsert_called["value"] = True
        return candidate_upsert_row

    def resume_upsert(candidate_id, resume_json):
        resume_upsert_called["value"] = True
        return existing_resume_row

    class FailingLLM:
        async def normalize_resume(self, input_data):
            llm_called["value"] = True
            raise AssertionError("LLM should not be called for empty resume text")

    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.get_by_email",
        lambda email: existing_candidate,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.get_by_candidate_id",
        lambda candidate_id: existing_resume_row,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.upsert",
        candidate_upsert,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.upsert",
        resume_upsert,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.SessionInitializer.initialize",
        lambda email: SessionBootstrapResult(
            candidate=candidate_upsert_row,
            resume=existing_resume_row,
            session=build_session(),
        ),
    )

    result = await ApplicationBootstrapService.bootstrap(
        email="zzhang32@usc.edu",
        name="Zhicheng Zhang",
        raw_resume_text="   ",
        llm=FailingLLM(),
    )

    assert result.is_new_candidate is False
    assert result.resume_updated is False
    assert result.used_existing_resume is True
    assert result.resume == existing_resume_row
    assert result.normalized_resume == CandidateResume.model_validate(
        existing_resume_row["resume_json"]
    )
    assert candidate_upsert_called["value"] is True
    assert resume_upsert_called["value"] is False
    assert llm_called["value"] is False


@pytest.mark.asyncio
async def test_bootstrap_reject_mismatch_falls_back_to_existing_resume(monkeypatch):
    existing_candidate = {
        "id": "candidate-001",
        "email": "zzhang32@usc.edu",
        "name": "Zhicheng Zhang",
    }

    existing_resume_row = {
        "candidate_id": "candidate-001",
        "resume_json": {
            "education": [
                {
                    "institution": "USC",
                    "program": "Computer Science",
                    "timeframe": "2025-2027",
                    "status": "current student",
                }
            ],
            "experiences": [],
            "skills": ["Python"],
        },
    }

    candidate_upsert_called = {"value": False}
    resume_upsert_called = {"value": False}
    llm_called = {"value": False}

    def candidate_upsert(candidate_id, email, name):
        candidate_upsert_called["value"] = True
        return {
            "id": candidate_id,
            "email": email,
            "name": name,
        }

    def resume_upsert(candidate_id, resume_json):
        resume_upsert_called["value"] = True
        return {
            "candidate_id": candidate_id,
            "resume_json": resume_json,
        }

    class FailingLLM:
        async def normalize_resume(self, input_data):
            llm_called["value"] = True
            raise AssertionError("LLM should not be called on mismatch fallback")

    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.get_by_email",
        lambda email: existing_candidate,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.get_by_candidate_id",
        lambda candidate_id: existing_resume_row,
    )
    monkeypatch.setattr(
        "app.server.interview.services.resume_preflight_analysis_service.ResumePreflightAnalysisService.analyze",
        lambda raw_resume_text, expected_email: ResumePreflightResult(
            decision=ResumeUpsertDecision.REJECT_MISMATCH,
            extracted_emails=["someone_else@example.com"],
            extracted_name="Someone Else",
            matched_sections=["education"],
            section_score=0.5,
            reasons=["resume contains a different email"],
        ),
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.upsert",
        candidate_upsert,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.upsert",
        resume_upsert,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.SessionInitializer.initialize",
        lambda email: SessionBootstrapResult(
            candidate=existing_candidate,
            resume=existing_resume_row,
            session=build_session(),
        ),
    )

    result = await ApplicationBootstrapService.bootstrap(
        email="zzhang32@usc.edu",
        name="Zhicheng Zhang",
        raw_resume_text="""
            Someone Else
            someone_else@example.com

            EDUCATION
            Example University

            EXPERIENCE
            Example Company

            SKILLS
            Python
        """,
        llm=FailingLLM(),
    )

    assert result.is_new_candidate is False
    assert result.resume_updated is False
    assert result.used_existing_resume is True
    assert result.resume == existing_resume_row
    assert result.normalized_resume == CandidateResume.model_validate(
        existing_resume_row["resume_json"]
    )
    assert candidate_upsert_called["value"] is False
    assert resume_upsert_called["value"] is False
    assert llm_called["value"] is False


@pytest.mark.asyncio
async def test_bootstrap_empty_resume_raises_without_existing_resume(monkeypatch):
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.CandidateRepository.get_by_email",
        lambda email: None,
    )
    monkeypatch.setattr(
        "app.server.interview.services.application_bootstrap_service.ResumeRepository.get_by_candidate_id",
        lambda candidate_id: None,
    )

    class DummyLLM:
        async def normalize_resume(self, input_data):
            raise AssertionError("LLM should not be called")

    with pytest.raises(ValueError, match="no existing resume exists"):
        await ApplicationBootstrapService.bootstrap(
            email="zzhang32@usc.edu",
            name="Zhicheng Zhang",
            raw_resume_text="   ",
            llm=DummyLLM(),
        )