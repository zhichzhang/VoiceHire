# app/server/interview/repositories/evidence_repository.py

from typing import Any

from app.server.core.supabase_client import supabase_client


class EvidenceRepository:
    @staticmethod
    def get_by_session_id(session_id: str) -> dict[str, Any] | None:
        response = (
            supabase_client.table("session_experience_evidence")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    @staticmethod
    def upsert(session_id: str, evidence_json: dict[str, Any]) -> dict[str, Any]:
        response = (
            supabase_client.table("session_experience_evidence")
            .upsert(
                {
                    "session_id": session_id,
                    "evidence_json": evidence_json,
                },
                on_conflict="session_id",
            )
            .execute()
        )
        return response.data[0]