# app/server/interview/repositories/candidate_repository.py

from typing import Any

from app.server.core.supabase_client import supabase_client


class CandidateRepository:
    @staticmethod
    def get_by_email(email: str) -> dict[str, Any] | None:
        response = (
            supabase_client.table("candidates")
            .select("*")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    @staticmethod
    def get_by_id(candidate_id: str) -> dict[str, Any] | None:
        response = (
            supabase_client.table("candidates")
            .select("*")
            .eq("id", candidate_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    @staticmethod
    def upsert(candidate_id: str, email: str, name: str) -> dict[str, Any]:
        response = (
            supabase_client.table("candidates")
            .upsert(
                {
                    "id": candidate_id,
                    "email": email,
                    "name": name,
                },
                on_conflict="email",
            )
            .execute()
        )
        return response.data[0]