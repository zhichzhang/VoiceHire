# app/server/interview/repositories/resume_repository.py

from typing import Any

from app.server.core.supabase_client import supabase_client


class ResumeRepository:
    @staticmethod
    def get_by_candidate_id(candidate_id: str) -> dict[str, Any] | None:
        response = (
            supabase_client.table("candidate_resumes")
            .select("*")
            .eq("candidate_id", candidate_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    @staticmethod
    def upsert(candidate_id: str, resume_json: dict[str, Any]) -> dict[str, Any]:
        response = (
            supabase_client.table("candidate_resumes")
            .upsert(
                {
                    "candidate_id": candidate_id,
                    "resume_json": resume_json,
                },
                on_conflict="candidate_id",
            )
            .execute()
        )
        return response.data[0]