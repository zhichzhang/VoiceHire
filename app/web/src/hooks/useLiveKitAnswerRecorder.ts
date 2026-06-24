import { useCallback, useEffect, useRef, useState } from "react";
import { Room, RoomEvent } from "livekit-client";

import {
  clearTranscriptionSession,
  createTranscribeToken,
  dispatchTranscriptionWorker,
  getParsedTranscript,
  startTranscriptionSession,
} from "../api/transcribeApi";

type RecorderStatus =
  | "idle"
  | "connecting"
  | "ready"
  | "recording"
  | "paused"
  | "disconnecting"
  | "error";

type ParsedTranscriptResponse = {
  session_id: string;
  active: boolean;
  latest_text: string;
  latest_is_final: boolean;
  final_text: string;
  parsed_text: string;
  chunk_count: number;
  final_chunk_count: number;
  final_chunks: Array<{
    chunk_id: string;
    text: string;
    is_final: boolean;
    created_at: string;
  }>;
  updated_at: string;
};

type CreateTranscribeTokenResponse = {
  url: string;
  room: string;
  identity: string;
  token: string;
};

type UseLiveKitAnswerRecorderOptions = {
  sessionId: string | null | undefined;
  autoConnect?: boolean;
  pollIntervalMs?: number;
};

type UseLiveKitAnswerRecorderReturn = {
  connected: boolean;
  status: RecorderStatus;
  micEnabled: boolean;
  audioLevel: number;
  participantCount: number;
  roomName: string;
  identity: string;
  transcript: string;
  latestIsFinal: boolean;
  loading: boolean;
  error: string | null;
  connect: () => Promise<void>;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string>;
  disconnect: () => Promise<void>;
  clearTranscript: () => void;
};

const DEFAULT_POLL_INTERVAL_MS = 500;
const AUDIO_LEVEL_POLL_MS = 80;

function normalizeTranscript(result: ParsedTranscriptResponse): string {
  return (result.parsed_text || result.final_text || "").trim();
}

export function useLiveKitAnswerRecorder(
  options: UseLiveKitAnswerRecorderOptions,
): UseLiveKitAnswerRecorderReturn {
  const {
    sessionId,
    autoConnect = true,
    pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
  } = options;

  const roomRef = useRef<Room | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const audioTimerRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);
  const sessionIdRef = useRef<string | null>(sessionId ?? null);
  const transcriptRef = useRef<string>("");
  const connectingRef = useRef(false);


  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [micEnabled, setMicEnabled] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [participantCount, setParticipantCount] = useState(0);
  const [roomName, setRoomName] = useState("");
  const [identity, setIdentity] = useState("");
  const [transcript, setTranscript] = useState("");
  const [latestIsFinal, setLatestIsFinal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stopTranscriptPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const stopAudioLevelPolling = useCallback(() => {
    if (audioTimerRef.current !== null) {
      window.clearInterval(audioTimerRef.current);
      audioTimerRef.current = null;
    }
  }, []);

  const readLatestTranscript = useCallback(async (): Promise<string> => {
    const currentSessionId = sessionIdRef.current;
    if (!currentSessionId) {
      return "";
    }

    const result = (await getParsedTranscript(
      currentSessionId,
    )) as ParsedTranscriptResponse;

    const nextTranscript = normalizeTranscript(result);

    if (isMountedRef.current) {
      transcriptRef.current = nextTranscript;
      setTranscript(nextTranscript);
      setLatestIsFinal(Boolean(result.latest_is_final));
    }

    return nextTranscript;
  }, []);

  const startTranscriptPolling = useCallback(() => {
    stopTranscriptPolling();

    void readLatestTranscript().catch(() => {
      // best effort
    });

    pollTimerRef.current = window.setInterval(() => {
      void readLatestTranscript().catch(() => {
        // best effort
      });
    }, pollIntervalMs);
  }, [pollIntervalMs, readLatestTranscript, stopTranscriptPolling]);

  const startAudioLevelPolling = useCallback(() => {
    stopAudioLevelPolling();

    audioTimerRef.current = window.setInterval(() => {
      const room = roomRef.current;
      if (!room) {
        return;
      }

      setAudioLevel(room.localParticipant.audioLevel ?? 0);
    }, AUDIO_LEVEL_POLL_MS);
  }, [stopAudioLevelPolling]);

  const resetCurrentAnswer = useCallback(() => {
    transcriptRef.current = "";
    setTranscript("");
    setLatestIsFinal(false);
  }, []);

  const waitForWorkerJoin = async (
    room: Room,
    timeoutMs = 10000,
  ): Promise<void> => {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
      console.log(
        "[WAIT WORKER]",
        room.remoteParticipants.size,
        room.numParticipants,
      );

      if (room.remoteParticipants.size > 0) {
        return;
      }

      await new Promise((resolve) => {
        window.setTimeout(resolve, 250);
      });
    }

    throw new Error(
      "Transcription worker did not join the room within timeout.",
    );
  };

  const connect = useCallback(async () => {
    const currentSessionId = sessionIdRef.current;

    if (!currentSessionId) {
      setError("sessionId is required.");
      setStatus("error");
      return;
    }

    // 防止重複 connect
    if (connectingRef.current) {
      return;
    }

    // 已經有 room 就直接返回
    if (roomRef.current) {
      return;
    }

    connectingRef.current = true;

    setLoading(true);
    setError(null);
    setStatus("connecting");

    try {
      await startTranscriptionSession({
        session_id: currentSessionId,
        reset: false,
      });

      const tokenPayload =
        await createTranscribeToken(
          currentSessionId,
        ) as CreateTranscribeTokenResponse;

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      room.on(RoomEvent.Connected, () => {
        if (!isMountedRef.current) return;

        setConnected(true);

        setParticipantCount(
          room.remoteParticipants.size,
        );

        setAudioLevel(
          room.localParticipant.audioLevel ?? 0,
        );
      });

      room.on(RoomEvent.Disconnected, () => {
        if (!isMountedRef.current) return;

        stopTranscriptPolling();
        stopAudioLevelPolling();

        setConnected(false);
        setMicEnabled(false);
        setParticipantCount(0);
        setAudioLevel(0);

        setStatus("idle");

        roomRef.current = null;
      });

      room.on(RoomEvent.ParticipantConnected, () => {
        if (!isMountedRef.current) return;

        setParticipantCount(
          room.remoteParticipants.size,
        );
      });

      room.on(RoomEvent.ParticipantDisconnected, () => {
        if (!isMountedRef.current) return;

        setParticipantCount(
          room.remoteParticipants.size,
        );
      });

      room.on(RoomEvent.LocalTrackPublished, () => {
        if (!isMountedRef.current) return;

        setMicEnabled(
          room.localParticipant.isMicrophoneEnabled,
        );

        setAudioLevel(
          room.localParticipant.audioLevel ?? 0,
        );
      });

      room.on(RoomEvent.LocalTrackUnpublished, () => {
        if (!isMountedRef.current) return;

        setMicEnabled(
          room.localParticipant.isMicrophoneEnabled,
        );

        setAudioLevel(
          room.localParticipant.audioLevel ?? 0,
        );
      });

      roomRef.current = room;

      setRoomName(tokenPayload.room);
      setIdentity(tokenPayload.identity);

      await room.connect(
        tokenPayload.url,
        tokenPayload.token,
      );

      await dispatchTranscriptionWorker(
        currentSessionId,
      );

      await waitForWorkerJoin(room);
      console.log(
        "[AFTER WAIT]",
        room.remoteParticipants.size,
        room.numParticipants,
      );

      if (!isMountedRef.current) {
        return;
      }

      setParticipantCount(
        room.remoteParticipants.size,
      );

      // 只有 worker 真正進房才算 ready
      setStatus("ready");
    } catch (connectError) {
      const message =
        connectError instanceof Error
          ? connectError.message
          : "Failed to connect LiveKit answer recorder.";

      if (isMountedRef.current) {
        setError(message);
        setStatus("error");
      }

      try {
        roomRef.current?.disconnect();
      } catch {
        // ignore
      }

      roomRef.current = null;

      setConnected(false);
      setMicEnabled(false);
      setParticipantCount(0);
      setAudioLevel(0);
    } finally {
      connectingRef.current = false;

      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [
    stopAudioLevelPolling,
    stopTranscriptPolling,
  ]);

  const startRecording = useCallback(async () => {
    const currentSessionId = sessionIdRef.current;

    if (!currentSessionId) {
      setError("sessionId is required.");
      setStatus("error");
      return;
    }

    try {
      if (!roomRef.current) {
        await connect();
      }

      const liveRoom = roomRef.current;

      if (!liveRoom) {
        throw new Error(
          "LiveKit room is not ready.",
        );
      }

      // Worker 必須存在
      if (liveRoom.remoteParticipants.size === 0) {
        throw new Error(
          "Transcription worker has not joined the room.",
        );
      }

      await startTranscriptionSession({
        session_id: currentSessionId,
        reset: true,
      });

      resetCurrentAnswer();

      startTranscriptPolling();

      if (
        !liveRoom.localParticipant.isMicrophoneEnabled
      ) {
        await liveRoom.localParticipant.setMicrophoneEnabled(
          true,
        );
      }

      setMicEnabled(true);

      setStatus("recording");

      setAudioLevel(
        liveRoom.localParticipant.audioLevel ?? 0,
      );

      startAudioLevelPolling();
    } catch (startError) {
      const message =
        startError instanceof Error
          ? startError.message
          : "Failed to start recording.";

      setError(message);
      setStatus("error");
    }
  }, [
    connect,
    resetCurrentAnswer,
    startAudioLevelPolling,
    startTranscriptPolling,
  ]);

  const stopRecording = useCallback(async (): Promise<string> => {
    const currentSessionId = sessionIdRef.current;
    const room = roomRef.current;

    if (!currentSessionId || !room) {
      return "";
    }

    try {
      if (room.localParticipant.isMicrophoneEnabled) {
        await room.localParticipant.setMicrophoneEnabled(false);
      }

      setMicEnabled(false);
      setAudioLevel(0);
      setStatus("paused");

      stopAudioLevelPolling();
      stopTranscriptPolling();

      await new Promise((resolve) => window.setTimeout(resolve, 150));

      const transcriptText = await readLatestTranscript();

      await clearTranscriptionSession(currentSessionId);

      transcriptRef.current = transcriptText;
      setTranscript(transcriptText);

      return transcriptText;
    } catch (stopError) {
      const message =
        stopError instanceof Error
          ? stopError.message
          : "Failed to stop recording.";

      setError(message);
      setStatus("error");
      return transcriptRef.current;
    }
  }, [
    readLatestTranscript,
    stopAudioLevelPolling,
    stopTranscriptPolling,
  ]);

  const disconnect = useCallback(async () => {
    const currentSessionId = sessionIdRef.current;
    const room = roomRef.current;

    setStatus("disconnecting");

    try {
      stopAudioLevelPolling();
      stopTranscriptPolling();

      if (room?.localParticipant.isMicrophoneEnabled) {
        await room.localParticipant.setMicrophoneEnabled(false);
      }

      if (currentSessionId) {
        await clearTranscriptionSession(currentSessionId);
      }

      room?.disconnect();
    } catch (disconnectError) {
      const message =
        disconnectError instanceof Error
          ? disconnectError.message
          : "Failed to disconnect recorder.";

      setError(message);
      setStatus("error");
    } finally {
      roomRef.current = null;
      setConnected(false);
      setMicEnabled(false);
      setParticipantCount(0);
      setAudioLevel(0);
      setRoomName("");
      setIdentity("");
      resetCurrentAnswer();
      setStatus("idle");
    }
  }, [
    resetCurrentAnswer,
    stopAudioLevelPolling,
    stopTranscriptPolling,
  ]);

  useEffect(() => {
    sessionIdRef.current = sessionId ?? null;
  }, [sessionId]);

  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      stopTranscriptPolling();
      stopAudioLevelPolling();
      roomRef.current?.disconnect();
      roomRef.current = null;
    };
  }, [stopAudioLevelPolling, stopTranscriptPolling]);

  useEffect(() => {
    if (!autoConnect || !sessionIdRef.current) {
      return;
    }

    if (roomRef.current || connected || loading) {
      return;
    }

    void connect();
  }, [autoConnect, connect, connected, loading]);

  return {
    connected,
    status,
    micEnabled,
    audioLevel,
    participantCount,
    roomName,
    identity,
    transcript,
    latestIsFinal,
    loading,
    error,
    connect,
    startRecording,
    stopRecording,
    disconnect,
    clearTranscript: resetCurrentAnswer,
  };
}