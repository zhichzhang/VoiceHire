# app/server/workers/livekit_stt_worker.py

from __future__ import annotations

import asyncio
from typing import Set

import httpx
from livekit import agents, rtc
from livekit.agents import AgentServer, inference
from livekit.agents.stt import SpeechEventType

from app.server.core.config import settings
from app.server.core.logger import logger

server = AgentServer()


def extract_session_id(room_name: str) -> str:
    prefix = settings.livekit_room_prefix
    if room_name.startswith(prefix):
        return room_name[len(prefix):]
    return room_name


async def post_json(client: httpx.AsyncClient, path: str, payload: dict) -> dict:
    resp = await client.post(path, json=payload)
    resp.raise_for_status()
    return resp.json()


async def publish_chunk(
    client: httpx.AsyncClient,
    session_id: str,
    text: str,
    is_final: bool,
) -> None:
    await post_json(
        client,
        f"/transcribe/sessions/{session_id}/chunks",
        {"text": text, "is_final": is_final},
    )


async def process_audio_track(
    track: rtc.RemoteTrack,
    session_id: str,
    client: httpx.AsyncClient,
) -> None:
    logger.livekit(f"[STT] PROCESS_AUDIO_TRACK session={session_id}")

    try:
        audio_stream = rtc.AudioStream(track)
    except Exception as exc:
        logger.warning(f"[STT] SKIP_NON_AUDIO_TRACK error={exc}")
        return

    stt = inference.STT(
        model=settings.livekit_stt_model,
        language=settings.livekit_stt_language,
    )
    stt_stream = stt.stream()

    async def pump_audio() -> None:
        async for audio_event in audio_stream:
            stt_stream.push_frame(audio_event.frame)
        stt_stream.end_input()

    async def pump_transcripts() -> None:
        try:
            async for event in stt_stream:
                if not event.alternatives:
                    continue

                text = event.alternatives[0].text.strip()
                if not text:
                    continue

                if event.type == SpeechEventType.INTERIM_TRANSCRIPT:
                    await publish_chunk(
                        client=client,
                        session_id=session_id,
                        text=text,
                        is_final=False,
                    )
                elif event.type == SpeechEventType.FINAL_TRANSCRIPT:
                    await publish_chunk(
                        client=client,
                        session_id=session_id,
                        text=text,
                        is_final=True,
                    )
        finally:
            await stt_stream.aclose()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(pump_audio())
        tg.create_task(pump_transcripts())


@server.rtc_session(agent_name="voicehire-transcriber")
async def transcriber(ctx: agents.JobContext):
    room_name = getattr(ctx.room, "name", "")
    session_id = extract_session_id(room_name)

    logger.livekit(f"[STT] ENTRY room={room_name} session={session_id}")

    async with httpx.AsyncClient(
        base_url=settings.voicehire_api_base_url,
        timeout=15.0,
    ) as client:
        await post_json(
            client,
            f"/transcribe/sessions/{session_id}/start",
            {"session_id": session_id, "reset": False},
        )

        processed_tracks: Set[str] = set()

        @ctx.room.on("track_subscribed")
        def on_track_subscribed(track: rtc.RemoteTrack):
            track_id = getattr(track, "sid", None) or str(id(track))
            if track_id in processed_tracks:
                return
            processed_tracks.add(track_id)
            asyncio.create_task(
                process_audio_track(
                    track=track,
                    session_id=session_id,
                    client=client,
                )
            )

        await asyncio.Event().wait()


if __name__ == "__main__":
    import os

    if settings.livekit_url:
        os.environ["LIVEKIT_URL"] = settings.livekit_url
    if settings.livekit_api_key:
        os.environ["LIVEKIT_API_KEY"] = settings.livekit_api_key
    if settings.livekit_api_secret:
        os.environ["LIVEKIT_API_SECRET"] = settings.livekit_api_secret

    agents.cli.run_app(server)
