# app/server/interview/engines/session_loader.py

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.server.interview.repositories.candidate_repository import (
    CandidateRepository,
)
from app.server.interview.repositories.evaluation_repository import (
    EvaluationRepository,
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
from app.server.interview.repositories.turn_repository import (
    TurnRepository,
)
from app.server.interview.sessions.session_initializer import SessionInitializer
from app.server.models.Interview_turn import (
    InterviewTurn,
)
from app.server.models.assessment import (
    TurnAssessment,
)
from app.server.models.candidate import (
    CandidateProfile,
)
from app.server.models.evaluation import (
    InterviewEvaluation,
)
from app.server.models.experience_evidence import (
    ExperienceEvidence,
)
from app.server.models.resume import (
    CandidateResume,
)
from app.server.models.session import (
    InterviewSession,
)


@dataclass
class LoadedSessionBundle:
    candidate: dict[str, Any] | None
    resume: dict[str, Any] | None
    session: InterviewSession


class SessionLoader:
    """
    Load a persisted interview session by session UUID.

    This is the main entrypoint for resume-by-UUID and
    resume-by-cookie flows.
    """

    @staticmethod
    def load(session_id: str) -> LoadedSessionBundle:
        session_row = SessionRepository.get_by_id(session_id)
        if not session_row:
            raise ValueError(
                f"Session not found: {session_id}"
            )

        candidate_id = session_row["candidate_id"]

        candidate = CandidateRepository.get_by_id(
            candidate_id
        )
        resume = ResumeRepository.get_by_candidate_id(
            candidate_id
        )

        profile_row = ProfileRepository.get_by_session_id(
            session_id
        )
        evidence_row = EvidenceRepository.get_by_session_id(
            session_id
        )
        evaluation_row = EvaluationRepository.get_by_session_id(
            session_id
        )
        turn_rows = TurnRepository.list_by_session_id(
            session_id
        )

        profile = (
            CandidateProfile.model_validate(
                profile_row["profile_json"]
            )
            if profile_row
            else CandidateProfile()
        )

        evidence = (
            ExperienceEvidence.model_validate(
                evidence_row["evidence_json"]
            )
            if evidence_row
            else ExperienceEvidence()
        )

        evaluation = (
            InterviewEvaluation.model_validate(
                evaluation_row["evaluation_json"]
            )
            if evaluation_row
            else None
        )

        resume_context = None

        if resume:
            resume_payload = resume["resume_json"]

            if isinstance(resume_payload, str):
                resume_payload = json.loads(resume_payload)

            resume_context = (
                SessionInitializer._build_resume_context(
                    resume_payload
                )
            )

        turns: list[InterviewTurn] = []
        for row in turn_rows:
            turns.append(
                InterviewTurn(
                    turn_number=row.get("turn_number"),
                    phase=row["phase"],
                    question=row["question"],
                    answer=row["answer"],
                    assessment=TurnAssessment(
                        relevance=_value_or_zero(
                            row.get("relevance")
                        ),
                        clarity=_value_or_zero(
                            row.get("clarity")
                        ),
                        fluency=_value_or_zero(
                            row.get("fluency")
                        ),
                    ),
                    assessment_status=row.get(
                        "assessment_status",
                        "pending",
                    ),
                    assessment_error=row.get(
                        "assessment_error",
                    ),
                    assessed_at=row.get(
                        "assessed_at",
                    ),
                )
            )

        session = InterviewSession(
            session_id=session_row["id"],
            current_phase=session_row["current_phase"],
            status=session_row.get("status", "active"),
            current_question=session_row.get(
                "current_question"
            ),
            current_answer=session_row.get(
                "current_answer"
            ),
            turns=turns,
            candidate_profile=profile,
            experience_evidence=evidence,
            evaluation=evaluation,
            resume_context=resume_context,
            started_at=session_row.get("started_at"),
            completed_at=session_row.get("completed_at"),
            expires_at=session_row.get("expires_at"),
        )

        return LoadedSessionBundle(
            candidate=candidate,
            resume=resume,
            session=session,
        )


def _value_or_zero(value: Any) -> float:
    return 0.0 if value is None else float(value)