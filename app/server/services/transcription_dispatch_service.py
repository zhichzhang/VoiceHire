# app/server/services/transcription_dispatch_service.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from livekit import api

# from app.server.core.config import settings
from app.server.core.config_docker import settings
from app.server.core.logger import logger


@dataclass(frozen=True)
class TranscriptionDispatchResult:
    ok: bool
    room: str
    agent_name: str
    dispatch_id: str
    already_dispatched: bool


class LiveKitTranscriptionDispatchService:
    """
    Explicitly dispatch the transcription worker into a LiveKit room.
    """

    def __init__(self) -> None:
        self._livekit_url = settings.livekit_url
        self._api_key = settings.livekit_api_key
        self._api_secret = settings.livekit_api_secret
        self._room_prefix = settings.livekit_room_prefix
        self._agent_name = (
            getattr(settings, "livekit_transcriber_agent_name", None)
            or os.getenv("LIVEKIT_TRANSCRIBER_AGENT_NAME", "voicehire-transcriber")
        )

    def _require_config(self) -> None:
        if not self._livekit_url:
            raise ValueError("LIVEKIT_URL is not configured.")
        if not self._api_key:
            raise ValueError("LIVEKIT_API_KEY is not configured.")
        if not self._api_secret:
            raise ValueError("LIVEKIT_API_SECRET is not configured.")

    def _room_name(self, session_id: str) -> str:
        return f"{self._room_prefix}{session_id}"

    async def dispatch(self, session_id: str) -> dict[str, object]:
        self._require_config()

        room_name = self._room_name(session_id)
        agent_name = self._agent_name

        logger.workflow(
            f"[TRANSCRIBE] DISPATCH_REQUEST session={session_id} "
            f"room={room_name} agent={agent_name}"
        )

        async with api.LiveKitAPI(
            url=self._livekit_url,
            api_key=self._api_key,
            api_secret=self._api_secret,
        ) as lkapi:
            existing_dispatches = await lkapi.agent_dispatch.list_dispatch(room_name)

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