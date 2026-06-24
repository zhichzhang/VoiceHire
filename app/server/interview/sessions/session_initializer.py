# app/server/interview/engines/session_initializer.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.server.core.logger import logger
from app.server.interview.repositories.candidate_repository import (
    CandidateRepository,
)
from app.server.interview.repositories.evidence_repository import (
    EvidenceRepository,
)
from app.server.interview.repositories.profile_repository import (
    ProfileRepository,
)
from app.server.interview.repositories.resume_repository import (
    ResumeRepository,
)
from app.server.interview.repositories.session_repository import (
    SessionRepository,
)
from app.server.llm.contracts.prompt_outputs import (
    EducationContext,
    HighlightedExperience,
)
from app.server.models.candidate import (
    CandidateProfile,
)
from app.server.models.experience_evidence import (
    ExperienceEvidence,
)
from app.server.models.resume import (
    CandidateResume,
    ResumeEducation,
    ResumeExperience,
)
from app.server.models.session import (
    InterviewSession,
)

DEFAULT_SESSION_TTL_DAYS = 7


@dataclass
class SessionBootstrapResult:
    candidate: dict[str, Any]
    resume: dict[str, Any]
    session: InterviewSession


class SessionInitializer:
    @staticmethod
    def _build_resume_context(resume_json: dict[str, Any]) -> CandidateResume:
        raw_education = resume_json.get("education", []) or []
        raw_experiences = (
            resume_json.get("experiences")
            or resume_json.get("experience", [])
            or []
        )
        raw_skills = resume_json.get("skills", []) or []

        logger.debug(
            f"[SESSION_INIT] build_resume_context "
            f"education={len(raw_education)} "
            f"experiences={len(raw_experiences)} "
            f"skills_type={type(raw_skills).__name__}"
        )

        education: list[ResumeEducation] = []
        for item in raw_education:
            education.append(
                ResumeEducation(
                    institution=item.get("institution")
                    or item.get("school")
                    or "",
                    program=item.get("program")
                    or item.get("degree")
                    or None,
                    timeframe=(
                        item.get("timeframe")
                        or item.get("expected_graduation")
                        or item.get("graduation_date")
                    ),
                    status=item.get("status"),
                )
            )

        experiences: list[ResumeExperience] = []
        for item in raw_experiences:
            summary = item.get("summary")
            if not summary:
                highlights = item.get("highlights", []) or []
                summary = " ".join(highlights) if highlights else ""

            skills = item.get("skills") or item.get("technologies") or []
            if not isinstance(skills, list):
                skills = [str(skills)]

            experiences.append(
                ResumeExperience(
                    name=item.get("title") or item.get("name") or "",
                    organization=item.get("company")
                    or item.get("organization"),
                    experience_type=item.get("experience_type"),
                    timeframe=(
                        item.get("timeframe")
                        or f'{item.get("start_date", "")} - {item.get("end_date", "")}'.strip()
                    ),
                    summary=summary or "",
                    skills=skills,
                )
            )

        if isinstance(raw_skills, dict):
            flattened_skills: list[str] = []
            for values in raw_skills.values():
                if isinstance(values, list):
                    flattened_skills.extend(str(v) for v in values)
        elif isinstance(raw_skills, list):
            flattened_skills = [str(v) for v in raw_skills]
        else:
            flattened_skills = []

        logger.debug(
            f"[SESSION_INIT] resume_context_ready "
            f"education={len(education)} "
            f"experiences={len(experiences)} "
            f"skills={len(flattened_skills)}"
        )

        return CandidateResume(
            education=education,
            experiences=experiences,
            skills=flattened_skills,
        )

    @staticmethod
    def _build_initial_profile(
        resume_context: CandidateResume,
    ) -> CandidateProfile:
        most_recent_role = None
        if resume_context.experiences:
            first_exp = resume_context.experiences[0]
            if first_exp.name and first_exp.organization:
                most_recent_role = f"{first_exp.name} at {first_exp.organization}"
            else:
                most_recent_role = first_exp.name or first_exp.organization

        education = None
        if resume_context.education:
            first_edu = resume_context.education[0]
            education = EducationContext(
                institution=first_edu.institution,
                program=first_edu.program,
                status=first_edu.status,
            )

        highlighted_experiences: list[HighlightedExperience] = []
        for exp in resume_context.experiences:
            highlighted_experiences.append(
                HighlightedExperience(
                    organization=exp.organization,
                    timeframe=exp.timeframe,
                    summary=exp.summary,
                    responsibilities=[],
                    achievements=[],
                )
            )

        domain_keywords = sorted(set(resume_context.skills))[:5]

        logger.debug(
            f"[SESSION_INIT] initial_profile "
            f"has_role={most_recent_role is not None} "
            f"has_education={education is not None} "
            f"highlighted_experiences={len(highlighted_experiences)} "
            f"domain_keywords={len(domain_keywords)}"
        )

        return CandidateProfile(
            most_recent_role=most_recent_role,
            education=education,
            highlighted_experiences=highlighted_experiences,
            domain_keywords=domain_keywords,
            other_context=[
                "Bootstrapped from resume before intro phase",
                f"Loaded {len(resume_context.education)} education entries",
                f"Loaded {len(resume_context.experiences)} experience entries",
            ],
        )

    @staticmethod
    def initialize(
        email: str,
        session_ttl_days: int = DEFAULT_SESSION_TTL_DAYS,
    ) -> SessionBootstrapResult:
        """
        Create a brand-new interview session from a candidate email.

        This is the entrypoint for starting a fresh interview.
        Resume-by-UUID should be handled by a separate loader.
        """
        logger.info(
            f"[SESSION_INIT] start email={email} "
            f"session_ttl_days={session_ttl_days}"
        )

        candidate = CandidateRepository.get_by_email(email)
        logger.database(
            f"[SESSION_INIT] candidate_lookup "
            f"email={email} "
            f"found={candidate is not None}"
        )
        if not candidate:
            raise ValueError(f"Candidate not found for email: {email}")

        resume = ResumeRepository.get_by_candidate_id(candidate["id"])
        logger.database(
            f"[SESSION_INIT] resume_lookup "
            f"candidate_id={candidate['id']} "
            f"found={resume is not None}"
        )
        if not resume:
            raise ValueError(
                f"Resume not found for candidate_id: {candidate['id']}"
            )

        resume_context = SessionInitializer._build_resume_context(
            resume["resume_json"]
        )
        profile = SessionInitializer._build_initial_profile(resume_context)

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=session_ttl_days)
        )

        logger.database(
            f"[SESSION_INIT] create_session "
            f"candidate_id={candidate['id']} "
            f"phase=intro"
        )

        session_row = SessionRepository.create(
            candidate_id=candidate["id"],
            current_phase="intro",
            status="active",
            current_question=None,
            current_answer=None,
            expires_at=expires_at,
        )

        logger.database(
            f"[SESSION_INIT] session_created "
            f"session_id={session_row['id']} "
            f"candidate_id={candidate['id']}"
        )

        ProfileRepository.upsert(
            session_row["id"],
            profile.model_dump(),
        )
        logger.database(
            f"[SESSION_INIT] profile_upserted "
            f"session_id={session_row['id']}"
        )

        EvidenceRepository.upsert(
            session_row["id"],
            ExperienceEvidence().model_dump(),
        )
        logger.database(
            f"[SESSION_INIT] evidence_upserted "
            f"session_id={session_row['id']}"
        )

        bootstrap_session = InterviewSession(
            session_id=session_row["id"],
            current_phase=session_row.get("current_phase", "intro"),
            status=session_row.get("status", "active"),
            current_question=session_row.get("current_question"),
            current_answer=session_row.get("current_answer"),
            turns=[],
            candidate_profile=profile,
            experience_evidence=ExperienceEvidence(),
            evaluation=None,
            resume_context=resume_context,
            started_at=session_row.get("started_at"),
            completed_at=session_row.get("completed_at"),
            expires_at=session_row.get("expires_at", expires_at),
        )

        logger.success(
            f"[SESSION_INIT] complete session_id={bootstrap_session.session_id}"
        )

        return SessionBootstrapResult(
            candidate=candidate,
            resume=resume,
            session=bootstrap_session,
        )