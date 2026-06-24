from __future__ import annotations

from uuid import uuid4

from app.server.services.transcript_composition_service import TranscriptCompositionService

"""
Transcription API.

This module is the control plane for the transcription bridge.

It is responsible for:
- Generating LiveKit tokens for browser clients
- Creating and maintaining transcription session state
- Dispatching the STT worker to the interview room
- Persisting transcript chunks produced by the STT worker
- Serving the latest transcript to frontend clients

Important:
Audio does not flow through these endpoints.
The actual audio path is handled by LiveKit + WebRTC.
Only transcript text is stored and served here.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from livekit import api

from app.server.core.config import settings
from app.server.core.logger import logger
from app.server.models.transcribe import (
    DeleteTranscriptionResponse,
    FinalizeTranscriptionRequest,
    LatestTranscriptResponse,
    StartTranscriptionRequest,
    TranscriptChunk,
    TranscriptChunkRequest,
    TokenRequest,
    TranscriptionSessionResponse,
    TranscriptionSessionState,
)

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

# ---------------------------------------------------------------------
# In-memory transcription store
# ---------------------------------------------------------------------

_TRANSCRIPTION_STORE: dict[str, TranscriptionSessionState] = {}
_STORE_LOCK = Lock()


# ---------------------------------------------------------------------
# Response model for parsed transcript output
# ---------------------------------------------------------------------

class ParsedTranscriptResponse(BaseModel):
    session_id: str
    active: bool
    latest_text: str
    latest_is_final: bool
    final_text: str
    parsed_text: str
    chunk_count: int
    final_chunk_count: int
    final_chunks: list[TranscriptChunk]
    updated_at: str


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_session(session_id: str) -> TranscriptionSessionState:
    session = _TRANSCRIPTION_STORE.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Transcription session '{session_id}' not found.",
        )
    return session


def _save_session(session: TranscriptionSessionState) -> TranscriptionSessionState:
    _TRANSCRIPTION_STORE[session.session_id] = session
    return session


def _require_livekit_config() -> tuple[str, str, str]:
    if not settings.livekit_url:
        raise HTTPException(status_code=500, detail="LIVEKIT_URL is not configured.")
    if not settings.livekit_api_key:
        raise HTTPException(status_code=500, detail="LIVEKIT_API_KEY is not configured.")
    if not settings.livekit_api_secret:
        raise HTTPException(status_code=500, detail="LIVEKIT_API_SECRET is not configured.")

    return (
        settings.livekit_url,
        settings.livekit_api_key,
        settings.livekit_api_secret,
    )


def _get_transcriber_agent_name() -> str:
    return (
        getattr(settings, "livekit_transcriber_agent_name", None)
        or os.getenv("LIVEKIT_TRANSCRIBER_AGENT_NAME", "voicehire-transcriber")
    )


def _is_not_found_error(exc: Exception) -> bool:
    status = getattr(exc, "status", None)
    code = getattr(exc, "code", None)
    message = str(exc).lower()

    return (
        status == 404
        or code == "not_found"
        or "requested room does not exist" in message
        or "not found" in message
    )


# def _compose_parsed_text(session: TranscriptionSessionState) -> tuple[str, str]:
#     """
#     Build:
#     - final_text: all finalized utterances joined together
#     - parsed_text: final_text + current interim if the current one is not final
#     """
#     final_chunks = [chunk for chunk in session.chunks if chunk.is_final]
#     final_text = " ".join(
#         chunk.text.strip() for chunk in final_chunks if chunk.text.strip()
#     ).strip()
#
#     latest_text = (session.latest_text or "").strip()
#
#     if (
#             latest_text
#             and not session.latest_is_final
#             and latest_text != final_text
#     ):
#         parsed_text = " ".join(part for part in [final_text, latest_text] if part).strip()
#     else:
#         parsed_text = final_text
#
#     return final_text, parsed_text


async def _dispatch_transcriber_to_room(session_id: str) -> dict[str, Any]:
    """
    Explicitly dispatch the STT worker into the interview room.
    """
    room_name = f"{settings.livekit_room_prefix}{session_id}"
    agent_name = _get_transcriber_agent_name()

    logger.workflow(
        f"[TRANSCRIBE] DISPATCH_REQUEST session={session_id} "
        f"room={room_name} agent={agent_name}"
    )

    lkapi = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    try:
        existing_dispatches = []
        try:
            existing_dispatches = await lkapi.agent_dispatch.list_dispatch(room_name)
        except Exception as exc:
            if _is_not_found_error(exc):
                logger.warning(
                    f"[TRANSCRIBE] LIST_DISPATCH_ROOM_NOT_FOUND session={session_id} "
                    f"room={room_name} proceeding_to_create=true error={exc}"
                )
                existing_dispatches = []
            else:
                raise

        for dispatch in existing_dispatches:
            if (
                getattr(dispatch, "agent_name", None) == agent_name
                and getattr(dispatch, "room", None) == room_name
            ):
                dispatch_id = getattr(dispatch, "id", "")
                logger.success(
                    f"[TRANSCRIBE] DISPATCH_ALREADY_EXISTS session={session_id} "
                    f"room={room_name} dispatch_id={dispatch_id}"
                )
                return {
                    "ok": True,
                    "room": room_name,
                    "agent_name": agent_name,
                    "dispatch_id": dispatch_id,
                    "already_dispatched": True,
                }

        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata=json.dumps(
                    {
                        "session_id": session_id,
                        "purpose": "transcription",
                    }
                ),
            )
        )

        dispatch_id = getattr(dispatch, "id", "")
        logger.success(
            f"[TRANSCRIBE] DISPATCH_CREATED session={session_id} "
            f"room={room_name} dispatch_id={dispatch_id}"
        )

        return {
            "ok": True,
            "room": room_name,
            "agent_name": agent_name,
            "dispatch_id": dispatch_id,
            "already_dispatched": False,
        }
    finally:
        await lkapi.aclose()


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------

@router.post("/token")
def create_token(payload: TokenRequest):
    logger.livekit(f"[TRANSCRIBE] CREATE_TOKEN session={payload.session_id}")

    livekit_url, api_key, api_secret = _require_livekit_config()

    room_name = f"{settings.livekit_room_prefix}{payload.session_id}"
    identity = f"candidate-{payload.session_id}"

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_ttl(timedelta(hours=1))
        .to_jwt()
    )

    logger.livekit(f"[TRANSCRIBE] TOKEN_CREATED room={room_name}")

    return {
        "url": livekit_url,
        "room": room_name,
        "identity": identity,
        "token": token,
    }


@router.post("/sessions/{session_id}/dispatch")
async def dispatch_transcription_worker(session_id: str):
    return await _dispatch_transcriber_to_room(session_id)


@router.post(
    "/sessions/{session_id}/start",
    response_model=TranscriptionSessionResponse,
)
def start_transcription_session(
    session_id: str,
    payload: StartTranscriptionRequest,
):
    logger.workflow(f"[TRANSCRIBE] START_SESSION session={session_id}")

    if payload.session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="Path session_id and body session_id do not match.",
        )

    with _STORE_LOCK:
        now = _utc_now_iso()

        if session_id in _TRANSCRIPTION_STORE and not payload.reset:
            session = _TRANSCRIPTION_STORE[session_id]
            session.active = True
            session.updated_at = now
            _save_session(session)

            logger.success(f"[TRANSCRIBE] SESSION_READY session={session_id}")
            return TranscriptionSessionResponse(session=session)

        session = TranscriptionSessionState(
            session_id=session_id,
            active=True,
            latest_text="",
            latest_is_final=False,
            updated_at=now,
            chunks=[],
        )
        _save_session(session)

        logger.success(f"[TRANSCRIBE] SESSION_READY session={session_id}")
        return TranscriptionSessionResponse(session=session)


@router.post(
    "/sessions/{session_id}/chunks",
    response_model=TranscriptionSessionResponse,
)
def ingest_transcription_chunk(
    session_id: str,
    payload: TranscriptChunkRequest,
):
    # logger.livekit(f"[TRANSCRIBE] CHUNK_RECEIVED session={session_id}")
    # logger.livekit(
    #     f"[TRANSCRIBE] CHUNK "
    #     f"text={payload.text!r} "
    #     f"is_final={payload.is_final}"
    # )

    with _STORE_LOCK:
        session = _ensure_session(session_id)
        now = _utc_now_iso()

        appended = TranscriptCompositionService.append_chunk(session, payload)

        if appended:
            logger.livekit(
                f"[TRANSCRIBE] CHUNK_STORED session={session_id} "
                f"total_chunks={len(session.chunks)}"
            )
        # else:
        #     logger.livekit(
        #         f"[TRANSCRIBE] CHUNK_DEDUPED session={session_id} "
        #         f"total_chunks={len(session.chunks)}"
        #     )

        _save_session(session)

        return TranscriptionSessionResponse(session=session)


@router.get(
    "/sessions/{session_id}",
    response_model=TranscriptionSessionResponse,
)
def get_transcription_session(session_id: str):
    logger.workflow(f"[TRANSCRIBE] GET_SESSION session={session_id}")

    with _STORE_LOCK:
        session = _ensure_session(session_id)
        return TranscriptionSessionResponse(session=session)


@router.get(
    "/sessions/{session_id}/latest",
    response_model=LatestTranscriptResponse,
)
def get_latest_transcript(session_id: str):
    logger.workflow(f"[TRANSCRIBE] GET_LATEST session={session_id}")

    with _STORE_LOCK:
        session = _ensure_session(session_id)

        return LatestTranscriptResponse(
            session_id=session.session_id,
            text=session.latest_text,
            is_final=session.latest_is_final,
            active=session.active,
            updated_at=session.updated_at,
            chunk_count=len(session.chunks),
        )


@router.get(
    "/sessions/{session_id}/result",
    response_model=ParsedTranscriptResponse,
)
def get_parsed_transcript_result(session_id: str):
    """
    Return a parsed transcript result suitable for UI display.

    - final_text: all finalized utterances
    - parsed_text: final_text + current interim if the latest chunk is not final
    """
    logger.workflow(f"[TRANSCRIBE] GET_RESULT session={session_id}")

    with _STORE_LOCK:
        session = _ensure_session(session_id)

        final_text, parsed_text = TranscriptCompositionService.compose_parsed_text(
            session
        )
        final_chunks = []

        previous_text = None

        for chunk in session.chunks:
            if not chunk.is_final:
                continue

            normalized = chunk.text.strip()

            if not normalized:
                continue

            if normalized == previous_text:
                continue

            final_chunks.append(chunk)

            previous_text = normalized

        return ParsedTranscriptResponse(
            session_id=session.session_id,
            active=session.active,
            latest_text=session.latest_text,
            latest_is_final=session.latest_is_final,
            final_text=final_text,
            parsed_text=parsed_text,
            chunk_count=len(session.chunks),
            final_chunk_count=len(final_chunks),
            final_chunks=final_chunks,
            updated_at=session.updated_at,
        )


@router.post(
    "/sessions/{session_id}/finalize",
    response_model=TranscriptionSessionResponse,
)
def finalize_transcription_session(
    session_id: str,
    payload: FinalizeTranscriptionRequest,
):
    logger.workflow(f"[TRANSCRIBE] FINALIZE session={session_id}")

    if payload.session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="Path session_id and body session_id do not match.",
        )

    with _STORE_LOCK:
        session = _ensure_session(session_id)
        session.active = False
        session.updated_at = _utc_now_iso()
        _save_session(session)

        logger.livekit(f"[TRANSCRIBE] SESSION_CLOSED session={session_id}")
        return TranscriptionSessionResponse(session=session)


@router.delete(
    "/sessions/{session_id}",
    response_model=DeleteTranscriptionResponse,
)
def delete_transcription_session(session_id: str):
    logger.warning(f"[TRANSCRIBE] DELETE_SESSION session={session_id}")

    with _STORE_LOCK:
        _ensure_session(session_id)
        del _TRANSCRIPTION_STORE[session_id]

    logger.success(f"[TRANSCRIBE] SESSION_DELETED session={session_id}")

    return DeleteTranscriptionResponse(deleted=True, session_id=session_id)

@router.post(
    "/sessions/{session_id}/clear",
    response_model=TranscriptionSessionResponse,
)
def clear_transcription_session(session_id: str):
    with _STORE_LOCK:
        session = _ensure_session(session_id)
        session.latest_text = ""
        session.latest_is_final = False
        session.chunks = []
        session.active = False
        session.updated_at = _utc_now_iso()
        _save_session(session)

        logger.success(f"[TRANSCRIBE] SESSION_CLEARED session={session_id}")
        return TranscriptionSessionResponse(session=session)

@router.get("/health")
def transcribe_health():
    logger.debug(f"[TRANSCRIBE] HEALTH_CHECK sessions={len(_TRANSCRIPTION_STORE)}")
    return {
        "ok": True,
        "provider": "backend-stt-bridge",
        "sessions": len(_TRANSCRIPTION_STORE),
    }