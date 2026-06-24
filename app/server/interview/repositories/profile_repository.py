# app/server/interview/repositories/profile_repository.py

from typing import Any

from app.server.core.supabase_client import supabase_client


class ProfileRepository:
    @staticmethod
    def get_by_session_id(session_id: str) -> dict[str, Any] | None:
        response = (
            supabase_client.table("session_profiles")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    @staticmethod
    def upsert(session_id: str, profile_json: dict[str, Any]) -> dict[str, Any]:
        response = (
            supabase_client.table("session_profiles")
            .upsert(
                {
                    "session_id": session_id,
                    "profile_json": profile_json,
                },
                on_conflict="session_id",
            )
            .execute()
        )
        return response.data[0]