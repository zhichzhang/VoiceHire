# # app/server/workers/livekit_agent.py
#
# from __future__ import annotations
#
# import asyncio
# from typing import AsyncIterable
#
# import httpx
# from livekit import agents, rtc
# from livekit.agents import AgentServer, inference
# from livekit.agents.stt import SpeechEvent, SpeechEventType
#
# from app.server.core.config import settings
# from app.server.core.logger import logger
#
#
# server = AgentServer()
#
#
# def extract_session_id(room_name: str) -> str:
#     """
#     Extract the interview session id from the LiveKit room name.
#
#     Convention:
#         voicehire-{session_id}
#     """
#     prefix = settings.livekit_room_prefix
#     if room_name.startswith(prefix):
#         return room_name[len(prefix):]
#     return room_name
#
#
# async def get_current_phase(
#     client: httpx.AsyncClient,
#     session_id: str,
# ) -> str:
#     """
#     Read the current phase from the interview session.
#     """
#     response = await client.get(f"/interview/sessions/{session_id}")
#     response.raise_for_status()
#     data = response.json()
#     session = data.get("session") or {}
#     return session.get("current_phase") or session.get("phase") or "intro"
#
#
# async def post_json(
#     client: httpx.AsyncClient,
#     path: str,
#     payload: dict,
# ) -> dict:
#     """
#     POST JSON to the backend and raise on HTTP errors.
#     """
#     response = await client.post(path, json=payload)
#     response.raise_for_status()
#     return response.json()
#
#
# async def publish_transcript_chunk(
#     client: httpx.AsyncClient,
#     session_id: str,
#     text: str,
#     is_final: bool,
#     phase: str,
# ) -> None:
#     """
#     Write one transcript chunk into the transcription bridge.
#     """
#     await post_json(
#         client,
#         f"/transcribe/sessions/{session_id}/chunks",
#         {
#             "text": text,
#             "is_final": is_final,
#             "phase": phase,
#         },
#     )
#
#
# async def process_stt_stream(
#     stream: AsyncIterable[SpeechEvent],
#     client: httpx.AsyncClient,
#     session_id: str,
#     phase: str,
# ) -> None:
#     """
#     Consume STT events and forward transcript text to the backend.
#     """
#     try:
#         async for event in stream:
#             if not event.alternatives:
#                 continue
#
#             text = event.alternatives[0].text.strip()
#             if not text:
#                 continue
#
#             if event.type == SpeechEventType.INTERIM_TRANSCRIPT:
#                 logger.livekit(
#                     f"[AGENT] INTERIM "
#                     f"len={len(text)} "
#                     f"text={text[:80]}"
#                 )
#                 await publish_transcript_chunk(
#                     client=client,
#                     session_id=session_id,
#                     text=text,
#                     is_final=False,
#                     phase=phase,
#                 )
#
#             elif event.type == SpeechEventType.FINAL_TRANSCRIPT:
#                 logger.livekit(
#                     f"[AGENT] FINAL "
#                     f"len={len(text)} "
#                     f"text={text[:120]}"
#                 )
#                 current_phase = await get_current_phase(client, session_id)
#
#                 # If the interview phase has advanced, sync the transcription bridge first.
#                 if current_phase != phase:
#                     await post_json(
#                         client,
#                         f"/transcribe/sessions/{session_id}/start",
#                         {
#                             "session_id": session_id,
#                             "phase": current_phase,
#                             "reset": False,
#                         },
#                     )
#                     phase = current_phase
#
#                 await publish_transcript_chunk(
#                     client=client,
#                     session_id=session_id,
#                     text=text,
#                     is_final=True,
#                     phase=phase,
#                 )
#
#                 await post_json(
#                     client,
#                     f"/interview/sessions/{session_id}/phases/{phase}/transcript",
#                     {
#                         "text": text,
#                     },
#                 )
#     finally:
#         await stream.aclose()
#
#
# async def process_audio_track(
#     track: rtc.RemoteTrack,
#     session_id: str,
#     initial_phase: str,
#     client: httpx.AsyncClient,
# ) -> None:
#     """
#     Read audio frames from one remote track and stream them into STT.
#     """
#     logger.livekit(
#         f"[AGENT] PROCESS_AUDIO_TRACK "
#         f"session={session_id}"
#     )
#
#     stt = inference.STT(
#         model=settings.livekit_stt_model,
#         language=settings.livekit_stt_language,
#     )
#     stt_stream = stt.stream()
#
#     try:
#         audio_stream = rtc.AudioStream(track)
#     except Exception as exc:
#         logger.warning(
#             f"[AGENT] SKIP_NON_AUDIO_TRACK "
#             f"error={exc}"
#         )
#         return
#
#     # Keep the latest known phase in a mutable holder so we can update it
#     # when the interview workflow advances to the next phase.
#     phase_state = {"value": initial_phase}
#
#     async def pump_audio() -> None:
#         """
#         Feed audio frames into the STT stream.
#         """
#         async for audio_event in audio_stream:
#             stt_stream.push_frame(audio_event.frame)
#
#         stt_stream.end_input()
#
#     async def pump_transcripts() -> None:
#         """
#         Consume STT events and forward transcript text to the backend.
#         """
#         try:
#             async for event in stt_stream:
#                 if not event.alternatives:
#                     continue
#
#                 text = event.alternatives[0].text.strip()
#                 if not text:
#                     continue
#
#                 if event.type == SpeechEventType.INTERIM_TRANSCRIPT:
#                     await publish_transcript_chunk(
#                         client=client,
#                         session_id=session_id,
#                         text=text,
#                         is_final=False,
#                         phase=phase_state["value"],
#                     )
#
#                 elif event.type == SpeechEventType.FINAL_TRANSCRIPT:
#                     # Re-read the current phase before persisting final text.
#                     current_phase = await get_current_phase(client, session_id)
#
#                     # If the interview has advanced, sync the transcription bridge.
#                     if current_phase != phase_state["value"]:
#                         await post_json(
#                             client,
#                             f"/transcribe/sessions/{session_id}/start",
#                             {
#                                 "session_id": session_id,
#                                 "phase": current_phase,
#                                 "reset": False,
#                             },
#                         )
#                         phase_state["value"] = current_phase
#
#                     await publish_transcript_chunk(
#                         client=client,
#                         session_id=session_id,
#                         text=text,
#                         is_final=True,
#                         phase=phase_state["value"],
#                     )
#
#                     # Forward the final transcript to the interview workflow.
#                     await post_json(
#                         client,
#                         f"/interview/sessions/{session_id}/phases/{phase_state['value']}/transcript",
#                         {
#                             "text": text,
#                         },
#                     )
#         finally:
#             await stt_stream.aclose()
#
#     async with asyncio.TaskGroup() as tg:
#         tg.create_task(pump_audio())
#         tg.create_task(pump_transcripts())
#
#
# @server.rtc_session(agent_name="voicehire-transcriber")
# async def transcriber(ctx: agents.JobContext):
#     """
#     LiveKit agent entrypoint.
#
#     This worker:
#     1. Joins the room
#     2. Derives the interview session id from the room name
#     3. Starts the transcription session on the backend
#     4. Streams audio into standalone STT
#     5. Pushes transcripts into /transcribe
#     6. Forwards final transcripts into /interview
#     """
#     room_name = getattr(ctx.room, "name", "")
#     session_id = extract_session_id(room_name)
#     logger.livekit(
#         f"[AGENT] ENTRYPOINT "
#         f"room={room_name} "
#         f"session={session_id}"
#     )
#
#     logger.livekit(
#         f"[AGENT] JOINED_ROOM "
#         f"room={room_name} "
#         f"session={session_id}"
#     )
#
#     async with httpx.AsyncClient(
#         base_url=settings.voicehire_api_base_url,
#         timeout=15.0,
#     ) as client:
#         # Read the current phase once at startup.
#         # The final transcript path will re-read the phase before submitting.
#         logger.livekit(
#             f"[AGENT] FETCH_PHASE "
#             f"session={session_id}"
#         )
#
#         initial_phase = await get_current_phase(
#             client,
#             session_id,
#         )
#
#         logger.livekit(
#             f"[AGENT] PHASE_READY "
#             f"phase={initial_phase}"
#         )
#
#         logger.livekit(
#             f"[AGENT] START_TRANSCRIPTION_SESSION "
#             f"session={session_id}"
#         )
#
#         await post_json(
#             client,
#             f"/transcribe/sessions/{session_id}/start",
#             {
#                 "session_id": session_id,
#                 "phase": initial_phase,
#                 "reset": False,
#             },
#         )
#         logger.success(
#             f"[AGENT] TRANSCRIPTION_SESSION_READY "
#             f"session={session_id}"
#         )
#
#         processed_tracks: set[str] = set()
#
#         @ctx.room.on("track_subscribed")
#         def on_track_subscribed(track: rtc.RemoteTrack):
#             """
#             Start a background task for each subscribed audio track.
#             """
#             logger.livekit(
#                 f"[AGENT] TRACK_SUBSCRIBED "
#                 f"session={session_id}"
#             )
#             track_id = getattr(track, "sid", None) or str(id(track))
#             if track_id in processed_tracks:
#                 return
#
#             processed_tracks.add(track_id)
#             asyncio.create_task(
#                 process_audio_track(
#                     track=track,
#                     session_id=session_id,
#                     initial_phase=initial_phase,
#                     client=client,
#                 )
#             )
#
#         # Keep the agent alive until the room disconnects.
#         await asyncio.Event().wait()
#
#
# import os
#
# if __name__ == "__main__":
#     if settings.livekit_url:
#         os.environ["LIVEKIT_URL"] = settings.livekit_url
#
#     if settings.livekit_api_key:
#         os.environ["LIVEKIT_API_KEY"] = settings.livekit_api_key
#
#     if settings.livekit_api_secret:
#         os.environ["LIVEKIT_API_SECRET"] = settings.livekit_api_secret
#
#     agents.cli.run_app(server)

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