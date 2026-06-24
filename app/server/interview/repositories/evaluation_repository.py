# app/server/interview/repositories/evaluation_repository.py

from typing import Any

from app.server.core.supabase_client import supabase_client


class EvaluationRepository:
    @staticmethod
    def get_by_session_id(session_id: str) -> dict[str, Any] | None:
        response = (
            supabase_client.table("session_evaluations")
            .select("*")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        return data[0] if data else None

    @staticmethod
    def upsert(session_id: str, evaluation_json: dict[str, Any]) -> dict[str, Any]:
        response = (
            supabase_client.table("session_evaluations")
            .upsert(
                {
                    "session_id": session_id,
                    "evaluation_json": evaluation_json,
                    "overall_score": evaluation_json["overall_score"],
                    "communication_score": evaluation_json["communication_score"],
                    "professional_score": evaluation_json["professional_score"],
                    "assessment_confidence": evaluation_json["assessment_confidence"],
                },
                on_conflict="session_id",
            )
            .execute()
        )
        return response.data[0]