from __future__ import annotations

"""
LiveKit STT Worker.

This worker is the media plane for transcription.

Responsibilities:
- Join the LiveKit room for an interview session
- Subscribe to the candidate's audio track
- Stream audio frames into the STT engine
- Forward interim/final transcript text back to the API layer

This worker does NOT:
- Manage interview logic
- Generate questions
- Evaluate answers
- Orchestrate phases

Its sole responsibility is speech-to-text.
"""

import asyncio
import os
from typing import Set, cast

import httpx
from livekit import agents, rtc
from livekit.agents import AgentServer, inference
from livekit.agents.stt import SpeechEventType

from app.server.core.config import settings
from app.server.core.logger import logger

server = AgentServer()


def extract_session_id(room_name: str) -> str:
    """
    Extract the interview session id from a LiveKit room name.

    Room naming convention:
        voicehire-{session_id}

    Example:
        voicehire-abc123 -> abc123
    """
    prefix = settings.livekit_room_prefix
    if room_name.startswith(prefix):
        return room_name[len(prefix):]
    return room_name


async def post_json(client: httpx.AsyncClient, path: str, payload: dict) -> dict:
    """
    Send a JSON POST request and raise on HTTP errors.
    """
    response = await client.post(path, json=payload)
    response.raise_for_status()
    return response.json()


async def publish_transcript_chunk(
    client: httpx.AsyncClient,
    session_id: str,
    text: str,
    is_final: bool,
) -> None:
    try:
        response = await client.post(
            f"/transcribe/sessions/{session_id}/chunks",
            json={
                "text": text,
                "is_final": is_final,
            },
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning(
            f"[STT] CHUNK_PUBLISH_FAILED session={session_id} error={exc}"
        )


async def process_audio_track(
    track: rtc.RemoteAudioTrack,
    session_id: str,
    client: httpx.AsyncClient,
) -> None:
    """
    Consume one LiveKit audio track and stream it into STT.
    """
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
        frame_count = 0

        try:
            async for audio_event in audio_stream:
                frame_count += 1

                frame = audio_event.frame

                if frame_count == 1:
                    logger.livekit(
                        f"[STT] FIRST_AUDIO_FRAME "
                        f"session={session_id}"
                    )

                # 每100幀打印一次
                if frame_count % 100 == 0:
                    logger.livekit(
                        f"[STT] AUDIO_FRAME "
                        f"session={session_id} "
                        f"count={frame_count} "
                        f"sample_rate={frame.sample_rate} "
                        f"samples={frame.samples_per_channel} "
                        f"channels={frame.num_channels}"
                    )

                stt_stream.push_frame(frame)

        finally:
            logger.livekit(
                f"[STT] AUDIO_STREAM_END "
                f"session={session_id} "
                f"frames={frame_count}"
            )

            try:
                stt_stream.end_input()
            except RuntimeError:
                pass

    async def pump_transcripts() -> None:
        """
        Consume STT output and forward transcript text to the API.
        """
        try:
            async for event in stt_stream:
                event_type = getattr(event.type, "name", str(event.type))

                logger.livekit(
                    f"[STT] STT_EVENT session={session_id} "
                    f"type={event_type} alts={len(event.alternatives)}"
                )

                if not event.alternatives:
                    continue

                alt = event.alternatives[0]

                logger.livekit(
                    f"[STT] ALT_RAW session={session_id} alt={alt!r}"
                )

                raw_text = alt.text
                text = raw_text.strip()

                logger.livekit(
                    f"[STT] STT_TEXT session={session_id} "
                    f"type={event_type} raw={raw_text!r} stripped={text!r}"
                )

                if not text:
                    continue

                if event_type.endswith("INTERIM_TRANSCRIPT"):
                    logger.livekit(
                        f"[STT] INTERIM session={session_id} "
                        f"len={len(text)} text={text[:80]}"
                    )
                    await publish_transcript_chunk(
                        client=client,
                        session_id=session_id,
                        text=text,
                        is_final=False,
                    )

                elif event_type.endswith("FINAL_TRANSCRIPT"):
                    logger.livekit(
                        f"[STT] FINAL session={session_id} "
                        f"len={len(text)} text={text[:120]}"
                    )
                    await publish_transcript_chunk(
                        client=client,
                        session_id=session_id,
                        text=text,
                        is_final=True
                    )
        except Exception as exc:
            logger.warning(
                f"[STT] PUMP_TRANSCRIPTS_ERROR session={session_id} error={exc}"
            )
            raise
        finally:
            try:
                stt_stream.end_input()
            except RuntimeError:
                pass

    async with asyncio.TaskGroup() as tg:
        tg.create_task(pump_audio())
        tg.create_task(pump_transcripts())


@server.rtc_session(agent_name="voicehire-transcriber")
async def transcriber(ctx: agents.JobContext):
    """
    LiveKit room entrypoint for the STT worker.
    """
    processed_tracks: Set[str] = set()

    async with httpx.AsyncClient(
        base_url=settings.voicehire_api_base_url,
        timeout=15.0,
    ) as client:

        @ctx.room.on("track_subscribed")
        def on_track_subscribed(track, *_) -> None:
            """
            Start a background task for each subscribed audio track.
            """
            try:
                if getattr(track, "kind", None) != rtc.TrackKind.KIND_AUDIO:
                    return

                audio_track = cast(rtc.RemoteAudioTrack, track)
                track_id = getattr(audio_track, "sid", None) or str(id(audio_track))

                if track_id in processed_tracks:
                    return

                processed_tracks.add(track_id)

                current_room_name = getattr(ctx.room, "name", "") or ""
                current_session_id = extract_session_id(current_room_name)

                logger.livekit(
                    f"[STT] TRACK_SUBSCRIBED session={current_session_id} "
                    f"track={track_id}"
                )

                asyncio.create_task(
                    process_audio_track(
                        track=audio_track,
                        session_id=current_session_id,
                        client=client,
                    )
                )
            except Exception as exc:
                logger.exception(
                    f"[STT] TRACK_SUBSCRIBED_HANDLER_ERROR error={exc}"
                )

        @ctx.room.on("track_unsubscribed")
        def on_track_unsubscribed(track, *_) -> None:
            """
            Log when a track ends or is removed.
            """
            try:
                track_id = getattr(track, "sid", None) or str(id(track))
                current_room_name = getattr(ctx.room, "name", "") or ""
                current_session_id = extract_session_id(current_room_name)

                logger.livekit(
                    f"[STT] TRACK_UNSUBSCRIBED session={current_session_id} "
                    f"track={track_id}"
                )
            except Exception as exc:
                logger.warning(
                    f"[STT] TRACK_UNSUBSCRIBED_HANDLER_ERROR error={exc}"
                )

        await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

        room_name = ctx.room.name or ""
        session_id = extract_session_id(room_name)

        logger.livekit(
            f"[STT] ENTRY room={room_name} session={session_id} "
            f"model={settings.livekit_stt_model} "
            f"language={settings.livekit_stt_language}"
        )

        await post_json(
            client,
            f"/transcribe/sessions/{session_id}/start",
            {
                "session_id": session_id,
                "reset": False,
            },
        )

        await asyncio.Event().wait()


if __name__ == "__main__":
    # When launched locally, export LiveKit credentials into env vars
    # so the agent runtime can resolve them normally.
    if settings.livekit_url:
        os.environ["LIVEKIT_URL"] = settings.livekit_url

    if settings.livekit_api_key:
        os.environ["LIVEKIT_API_KEY"] = settings.livekit_api_key

    if settings.livekit_api_secret:
        os.environ["LIVEKIT_API_SECRET"] = settings.livekit_api_secret

    agents.cli.run_app(server)