# app/server/interview/repositories/turn_repository.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.server.core.supabase_client import supabase_client


class TurnRepository:
    @staticmethod
    def list_by_session_id(session_id: str) -> list[dict[str, Any]]:
        response = (
            supabase_client.table("interview_turns")
            .select("*")
            .eq("session_id", session_id)
            .order("turn_number", desc=False)
            .execute()
        )
        return response.data or []

    @staticmethod
    def add_turn(
        session_id: str,
        turn_number: int,
        phase: str,
        question: str,
        answer: str,
        relevance: float | None = None,
        clarity: float | None = None,
        fluency: float | None = None,
        assessment_status: str = "pending",
        assessment_error: str | None = None,
        assessed_at: datetime | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "session_id": session_id,
            "turn_number": turn_number,
            "phase": phase,
            "question": question,
            "answer": answer,
            "relevance": relevance,
            "clarity": clarity,
            "fluency": fluency,
            "assessment_status": assessment_status,
            "assessment_error": assessment_error,
            "assessed_at": assessed_at.isoformat() if assessed_at else None,
        }
        response = (
            supabase_client.table("interview_turns")
            .upsert(payload, on_conflict="session_id,turn_number")
            .execute()
        )
        return response.data[0]

    @staticmethod
    def update_assessment(
        session_id: str,
        turn_number: int,
        relevance: float,
        clarity: float,
        fluency: float,
    ) -> dict[str, Any]:
        payload = {
            "relevance": relevance,
            "clarity": clarity,
            "fluency": fluency,
            "assessment_status": "completed",
            "assessment_error": None,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }
        response = (
            supabase_client.table("interview_turns")
            .update(payload)
            .eq("session_id", session_id)
            .eq("turn_number", turn_number)
            .execute()
        )
        return response.data[0]

    @staticmethod
    def mark_assessment_processing(
        session_id: str,
        turn_number: int,
    ) -> None:
        (
            supabase_client.table("interview_turns")
            .update(
                {
                    "assessment_status": "processing",
                    "assessment_error": None,
                }
            )
            .eq("session_id", session_id)
            .eq("turn_number", turn_number)
            .execute()
        )

    @staticmethod
    def mark_assessment_failed(
        session_id: str,
        turn_number: int,
        error: str,
    ) -> None:
        (
            supabase_client.table("interview_turns")
            .update(
                {
                    "assessment_status": "failed",
                    "assessment_error": error,
                    "assessed_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("session_id", session_id)
            .eq("turn_number", turn_number)
            .execute()
        )

    @staticmethod
    def count_incomplete_assessments(
            session_id: str,
    ) -> int:
        response = (
            supabase_client.table("interview_turns")
            .select(
                "session_id",
                count="exact",
            )
            .eq("session_id", session_id)
            .neq(
                "assessment_status",
                "completed",
            )
            .execute()
        )

        return response.count or 0