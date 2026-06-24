# app/server/interview/repositories/session_repository.py

import uuid
from datetime import datetime
from typing import Any

from app.server.core.supabase_client import supabase_client


class SessionRepository:
    """
    Repository responsible for persisting interview session state.

    Session state includes:

    - Current phase
    - Session status
    - Pending question
    - Pending answer
    - Resume expiration
    """

    @staticmethod
    def create(
        candidate_id: str,
        current_phase: str = "intro",
        status: str = "active",
        current_question: str | None = None,
        current_answer: str | None = None,
        expires_at: datetime | None = None,
    ) -> dict[str, Any]:

        session_id = str(uuid.uuid4())

        response = (
            supabase_client.table("interview_sessions")
            .insert(
                {
                    "id": session_id,
                    "candidate_id": candidate_id,
                    "current_phase": current_phase,
                    "status": status,
                    "current_question": current_question,
                    "current_answer": current_answer,
                    "expires_at": (
                        expires_at.isoformat()
                        if expires_at
                        else None
                    ),
                }
            )
            .execute()
        )

        return response.data[0]

    @staticmethod
    def get_by_id(
        session_id: str,
    ) -> dict[str, Any] | None:

        response = (
            supabase_client.table("interview_sessions")
            .select("*")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )

        data = response.data or []

        return data[0] if data else None

    @staticmethod
    def update_phase(
        session_id: str,
        current_phase: str,
    ) -> dict[str, Any]:

        response = (
            supabase_client.table("interview_sessions")
            .update(
                {
                    "current_phase": current_phase,
                }
            )
            .eq("id", session_id)
            .execute()
        )

        return response.data[0]

    @staticmethod
    def update_status(
        session_id: str,
        status: str,
    ) -> dict[str, Any]:

        response = (
            supabase_client.table("interview_sessions")
            .update(
                {
                    "status": status,
                }
            )
            .eq("id", session_id)
            .execute()
        )

        return response.data[0]

    @staticmethod
    def update_current_question(
        session_id: str,
        question: str | None,
    ) -> dict[str, Any]:

        response = (
            supabase_client.table("interview_sessions")
            .update(
                {
                    "current_question": question,
                }
            )
            .eq("id", session_id)
            .execute()
        )

        return response.data[0]

    @staticmethod
    def update_current_answer(
        session_id: str,
        answer: str | None,
    ) -> dict[str, Any]:

        response = (
            supabase_client.table("interview_sessions")
            .update(
                {
                    "current_answer": answer,
                }
            )
            .eq("id", session_id)
            .execute()
        )

        return response.data[0]

    @staticmethod
    def update_expiration(
        session_id: str,
        expires_at: datetime,
    ) -> dict[str, Any]:

        response = (
            supabase_client.table("interview_sessions")
            .update(
                {
                    "expires_at": expires_at.isoformat(),
                }
            )
            .eq("id", session_id)
            .execute()
        )

        return response.data[0]

    @staticmethod
    def complete(
        session_id: str,
    ) -> dict[str, Any]:

        response = (
            supabase_client.table("interview_sessions")
            .update(
                {
                    "status": "completed",
                    "current_question": None,
                    "current_answer": None,
                    "completed_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("id", session_id)
            .execute()
        )

        return response.data[0]

    @staticmethod
    def delete(
        session_id: str,
    ) -> None:
        """
        Delete an interview session.

        All dependent data will be automatically removed
        through ON DELETE CASCADE:

        - interview_turns
        - session_profiles
        - session_experience_evidence
        - session_evaluations
        """

        (
            supabase_client.table("interview_sessions")
            .delete()
            .eq("id", session_id)
            .execute()
        )