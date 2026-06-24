# app/server/models/transcribe.py

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """
    Request body for creating a LiveKit token.

    The frontend sends the interview session id
    so the backend can derive the room name.
    """

    session_id: str = Field(..., description="Interview session UUID.")


class StartTranscriptionRequest(BaseModel):
    """
    Request body for starting or resetting a transcription session.

    The STT worker and/or frontend may call this endpoint to ensure
    the transcription state exists before audio starts flowing.
    """

    session_id: str = Field(..., description="Interview session UUID.")
    reset: bool = Field(
        default=False,
        description="Whether to reset the session state.",
    )


class TranscriptChunkRequest(BaseModel):
    """
    Request body for storing one transcript fragment.

    This is produced by the STT worker and stored by the API layer.
    """

    text: str = Field(..., description="Transcript text from STT.")
    is_final: bool = Field(
        default=False,
        description="Whether this chunk is final.",
    )


class FinalizeTranscriptionRequest(BaseModel):
    """
    Request body for marking a transcription session inactive.
    """

    session_id: str = Field(..., description="Interview session UUID.")


class TranscriptChunk(BaseModel):
    """
    One stored transcript fragment.

    Chunks are appended in arrival order and preserve
    the transcript history for the session.
    """

    chunk_id: str
    text: str
    is_final: bool
    created_at: str


class TranscriptionSessionState(BaseModel):
    """
    In-memory transcription session state.

    This is the canonical runtime object stored by the API layer.

    Responsibilities:
    - Track whether the session is active
    - Store the latest transcript text
    - Preserve all transcript chunks
    - Provide lightweight state for frontend polling
    """

    session_id: str
    active: bool = True
    latest_text: str = ""
    latest_is_final: bool = False
    updated_at: str
    chunks: list[TranscriptChunk] = Field(default_factory=list)


class TranscriptionSessionResponse(BaseModel):
    """
    Standard response wrapper for transcription session endpoints.
    """

    session: TranscriptionSessionState


class LatestTranscriptResponse(BaseModel):
    """
    Lightweight response returned to the frontend polling loop.

    This intentionally avoids sending the full chunk history to
    keep payloads small and frequent polling cheap.
    """

    session_id: str
    text: str
    is_final: bool
    active: bool
    updated_at: str
    chunk_count: int


class DeleteTranscriptionResponse(BaseModel):
    """
    Response returned when a transcription session is deleted.
    """

    deleted: bool
    session_id: str