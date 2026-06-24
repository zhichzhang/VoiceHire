import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  Room,
  RoomEvent,
  type RemoteParticipant,
} from "livekit-client";

import {
  clearTranscriptionSession,
  createTranscribeToken,
  dispatchTranscriptionWorker,
  getParsedTranscript,
  startTranscriptionSession,
} from "../../api/transcribeApi";

type LogLevel = "info" | "success" | "warning" | "error";

type LogEntry = {
  ts: string;
  level: LogLevel;
  message: string;
};

type TokenPayload = {
  url: string;
  room: string;
  identity: string;
  token: string;
};

function timestamp(): string {
  return new Date().toLocaleTimeString();
}

function pushLog(
  setLogs: Dispatch<SetStateAction<LogEntry[]>>,
  level: LogLevel,
  message: string,
): void {
  setLogs((current) => [
    {
      ts: timestamp(),
      level,
      message,
    },
    ...current,
  ]);
}

function levelChipStyle(level: LogLevel): CSSProperties {
  switch (level) {
    case "success":
      return { background: "#dcfce7", color: "#166534" };
    case "warning":
      return { background: "#fef3c7", color: "#92400e" };
    case "error":
      return { background: "#fee2e2", color: "#991b1b" };
    default:
      return { background: "#e0e7ff", color: "#3730a3" };
  }
}

export default function DevAudioPageLivekit() {
  const roomRef = useRef<Room | null>(null);
  const pollRef = useRef<number | null>(null);

  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);
  const [connectionState, setConnectionState] = useState<
    "disconnected" | "connecting" | "connected"
  >("disconnected");
  const [connected, setConnected] = useState(false);
  const [micEnabled, setMicEnabled] = useState(false);
  const [roomName, setRoomName] = useState("");
  const [identity, setIdentity] = useState("");
  const [participantCount, setParticipantCount] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [tokenInfo, setTokenInfo] = useState<TokenPayload | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [latestTranscript, setLatestTranscript] = useState("");
  const [latestIsFinal, setLatestIsFinal] = useState(false);
  const [pauseSummary, setPauseSummary] = useState("");
  const activeSessionIdRef = useRef("");

  useEffect(() => {
      console.log(
        "[STATE] micEnabled changed",
        micEnabled,
      );
    }, [micEnabled]);

    useEffect(() => {
      console.log(
        "[STATE] latestTranscript changed",
        latestTranscript,
      );
    }, [latestTranscript]);

    useEffect(() => {
      console.log(
        "[STATE] pauseSummary changed",
        pauseSummary,
      );
    }, [pauseSummary]);


  const stopTranscriptPolling = () => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startTranscriptPolling = (cleanedSessionId: string) => {
    stopTranscriptPolling();

    const tick = async () => {
      try {
        const result = await getParsedTranscript(cleanedSessionId);
        setLatestTranscript(result.parsed_text ?? "");
        setLatestIsFinal(Boolean(result.latest_is_final));
      } catch (error) {
        pushLog(
          setLogs,
          "warning",
          error instanceof Error ? error.message : "Transcript polling failed.",
        );
      }
    };

    void tick();
    pollRef.current = window.setInterval(() => {
      void tick();
    }, 500);
  };

  const resetConnectedState = () => {
    setConnectionState("disconnected");
    setConnected(false);
    setMicEnabled(false);
    setParticipantCount(0);
    setAudioLevel(0);
  };

  const cleanupRoom = async () => {
    stopTranscriptPolling();

    const room = roomRef.current;
    roomRef.current = null;

    if (!room) {
      return;
    }

    try {
      await room.localParticipant.setMicrophoneEnabled(false);
    } catch {
      // Best effort cleanup.
    }

    try {
      room.disconnect();
    } catch {
      // Best effort cleanup.
    }
  };

  const syncStats = (room: Room) => {
    setConnectionState("connected");
    setConnected(true);
    setMicEnabled(room.localParticipant.isMicrophoneEnabled);
    setAudioLevel(room.localParticipant.audioLevel ?? 0);
    setParticipantCount(room.remoteParticipants.size);
  };

  const resetCurrentAnswerView = () => {
    setLatestTranscript("");
    setLatestIsFinal(false);
  };

  const bootstrapRoom = async () => {
  const cleanedSessionId = sessionId.trim();
  activeSessionIdRef.current = cleanedSessionId;

  if (!cleanedSessionId) {
    pushLog(setLogs, "warning", "Please enter a session id first.");
    return;
  }

  setLoading(true);

  try {
    pushLog(setLogs, "info", "Cleaning up existing room...");
    await cleanupRoom();
    pushLog(setLogs, "success", "Cleanup complete.");

    resetCurrentAnswerView();
    setPauseSummary("");
    setTokenInfo(null);
    setRoomName("");
    setIdentity("");

    pushLog(setLogs, "info", "Preparing transcription session...");
    await startTranscriptionSession({
      session_id: cleanedSessionId,
      reset: false,
    });
    pushLog(setLogs, "success", "Transcription session ready.");

    pushLog(setLogs, "info", "Requesting LiveKit token...");
    const payload = await createTranscribeToken(cleanedSessionId);

    setTokenInfo(payload);
    setRoomName(payload.room);
    setIdentity(payload.identity);
    setConnectionState("connecting");
    setConnected(false);
    setMicEnabled(false);
    setParticipantCount(0);
    setAudioLevel(0);

    const room = new Room({
      adaptiveStream: true,
      dynacast: true,
    });

    room.on(RoomEvent.Connected, () => {
      pushLog(setLogs, "success", "Connected to LiveKit room.");
      syncStats(room);
    });

    room.on(RoomEvent.Disconnected, () => {
      pushLog(setLogs, "warning", "Disconnected from LiveKit room.");
      stopTranscriptPolling();
      resetConnectedState();
    });

    room.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
      pushLog(setLogs, "success", `Participant joined: ${participant.identity}`);
      setParticipantCount(room.remoteParticipants.size);
    });

    room.on(RoomEvent.ParticipantDisconnected, (participant: RemoteParticipant) => {
      pushLog(setLogs, "warning", `Participant left: ${participant.identity}`);
      setParticipantCount(room.remoteParticipants.size);
    });

    room.on(RoomEvent.LocalTrackPublished, () => {
      pushLog(setLogs, "success", "Local audio track published.");
      setMicEnabled(room.localParticipant.isMicrophoneEnabled);
      setAudioLevel(room.localParticipant.audioLevel ?? 0);
    });

    roomRef.current = room;

    pushLog(setLogs, "info", `Connecting to LiveKit room ${payload.room}...`);
    await room.connect(payload.url, payload.token);

    pushLog(setLogs, "info", "Dispatching STT worker...");
    try {
      await dispatchTranscriptionWorker(cleanedSessionId);
      pushLog(setLogs, "success", "STT worker dispatched.");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to dispatch STT worker.";
      pushLog(setLogs, "error", message);
    }

    startTranscriptPolling(cleanedSessionId);
    pushLog(setLogs, "success", "Room ready. Use Start answering to enable mic.");
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to bootstrap LiveKit.";
    pushLog(setLogs, "error", message);
    await cleanupRoom();

    setConnectionState("disconnected");
    setConnected(false);
    setMicEnabled(false);
    setParticipantCount(0);
    setAudioLevel(0);
    setTokenInfo(null);
    setRoomName("");
    setIdentity("");
  } finally {
    setLoading(false);
  }
};

  const startAnswering = async () => {
  const room = roomRef.current;
  const cleanedSessionId = activeSessionIdRef.current;

  console.log("[START] before enable", {
    micEnabledState: micEnabled,
    livekitMicEnabled: room?.localParticipant.isMicrophoneEnabled,
    connected,
  });

  if (!room || !cleanedSessionId) {
    pushLog(setLogs, "warning", "Bootstrap a room first.");
    return;
  }

  try {
    await clearTranscriptionSession(cleanedSessionId);
    resetCurrentAnswerView();
    setPauseSummary("");

    if (!room.localParticipant.isMicrophoneEnabled) {
      pushLog(setLogs, "info", "Enabling microphone...");
      await room.localParticipant.setMicrophoneEnabled(true);
    }

    console.log("[START] after enable", {
      livekitMicEnabled: room.localParticipant.isMicrophoneEnabled,
    });

    setMicEnabled(true);
    setAudioLevel(room.localParticipant.audioLevel ?? 0);

    pushLog(setLogs, "success", "Answering mode active.");
  } catch (error) {
    console.error("[START ERROR]", error);

    const message =
      error instanceof Error ? error.message : "Failed to enable microphone.";

    pushLog(setLogs, "error", message);
  }
};

  const pauseAnswering = async () => {
  const room = roomRef.current;
  const cleanedSessionId = activeSessionIdRef.current;

  if (!room || !cleanedSessionId) {
    return;
  }

  try {
    if (room.localParticipant.isMicrophoneEnabled) {
      pushLog(setLogs, "info", "Pausing microphone...");
      await room.localParticipant.setMicrophoneEnabled(false);
    }

    console.log("[PAUSE] after disable", {
      livekitMicEnabled: room.localParticipant.isMicrophoneEnabled,
    });

    setMicEnabled(false);
    setAudioLevel(0);

    const result = await getParsedTranscript(cleanedSessionId);
    const transcript = result.parsed_text ?? result.final_text ?? "";

    console.log("[PAUSE] parsed transcript", result);

    setPauseSummary(transcript);

    // 这里接你的 turn 存储接口
    // await saveTurnText(currentTurnId, transcript);

    await clearTranscriptionSession(cleanedSessionId);
    resetCurrentAnswerView();

    pushLog(setLogs, "success", "Answering paused.");
  } catch (error) {
    console.error("[PAUSE ERROR]", error);

    const message =
      error instanceof Error ? error.message : "Failed to pause microphone.";

    pushLog(setLogs, "error", message);
  }
};

  const endSession = async () => {
  const cleanedSessionId = activeSessionIdRef.current;

  try {
    if (roomRef.current?.localParticipant.isMicrophoneEnabled) {
      await roomRef.current.localParticipant.setMicrophoneEnabled(false);
    }

    if (cleanedSessionId) {
      await clearTranscriptionSession(cleanedSessionId);
    }
  } catch {
    // best effort
  }

  await cleanupRoom();
  setConnectionState("disconnected");
  setConnected(false);
  setMicEnabled(false);
  setParticipantCount(0);
  setAudioLevel(0);
  resetCurrentAnswerView();
  setPauseSummary("");
  setTokenInfo(null);
  setRoomName("");
  setIdentity("");

  pushLog(setLogs, "warning", "Session ended.");
};

  useEffect(() => {
    return () => {
      void cleanupRoom();
    };
  }, []);

  const connectionBadge = useMemo(() => {
    if (loading) return "connecting";
    if (connectionState === "connected" && micEnabled) return "answering";
    if (connectionState === "connected" && !micEnabled) return "room-ready";
    return "disconnected";
  }, [connectionState, loading, micEnabled]);

  return (
    <div style={styles.page}>
      <div style={styles.shell}>
        <section style={styles.card}>
          <div style={styles.kicker}>Dev Audio / LiveKit</div>
          <h1 style={styles.title}>LiveKit mic + STT test</h1>
          <p style={styles.subtext}>
            Bootstrap the room once, start and pause answering without tearing
            down the room, and keep transcript polling alive across question
            turns.
          </p>

          <div style={styles.grid}>
            <label style={styles.field}>
              <span style={styles.label}>Session ID</span>
              <input
                style={styles.input}
                value={sessionId}
                onChange={(event) => setSessionId(event.target.value)}
                placeholder="Paste interview session id"
                autoComplete="off"
              />
            </label>

            <label style={styles.field}>
              <span style={styles.label}>Room</span>
              <input
                style={styles.input}
                value={roomName}
                readOnly
                placeholder="voicehire-..."
              />
            </label>

            <label style={styles.field}>
              <span style={styles.label}>Identity</span>
              <input
                style={styles.input}
                value={identity}
                readOnly
                placeholder="candidate-..."
              />
            </label>

            <label style={styles.field}>
              <span style={styles.label}>Workflow</span>
              <input style={styles.input} value={connectionBadge} readOnly />
            </label>
          </div>

          <div style={styles.metrics}>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Participants</div>
              <div style={styles.metricValue}>{participantCount}</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Mic enabled</div>
              <div style={styles.metricValue}>{String(micEnabled)}</div>
            </div>
            <div style={styles.metricCard}>
              <div style={styles.metricLabel}>Audio level</div>
              <div style={styles.metricValue}>
                {Math.round(audioLevel * 100)}%
              </div>
            </div>
          </div>

          <div style={styles.metricCard}>
            <div style={styles.metricLabel}>Latest transcript</div>
            <div style={styles.transcriptValue}>
              {latestTranscript || "Waiting for speech..."}
            </div>
            <div style={styles.transcriptStatus}>
              {latestIsFinal ? "final" : "interim"}
            </div>
          </div>

          <div style={styles.metricCard}>
            <div style={styles.metricLabel}>Pause summary</div>
            <div style={styles.transcriptValue}>
              {pauseSummary || "Pause to capture a summarized transcript."}
            </div>
          </div>

          <div style={styles.buttonRow}>
            <button
              type="button"
              style={styles.primaryButton}
              onClick={() => void bootstrapRoom()}
              disabled={loading}
            >
              {loading ? "Bootstrapping..." : "Bootstrap room"}
            </button>

            <button
              type="button"
              style={styles.secondaryButton}
              onClick={() => void startAnswering()}
              disabled={!connected || micEnabled}
            >
              Start answering
            </button>

            <button
              type="button"
              style={styles.secondaryButton}
              onClick={() => void pauseAnswering()}
              disabled={!connected || !micEnabled}
            >
              Pause answering
            </button>

            <button
              type="button"
              style={styles.dangerButton}
              onClick={() => void endSession()}
            >
              End session
            </button>
          </div>

          {tokenInfo ? (
            <div style={styles.tokenBox}>
              <div style={styles.tokenTitle}>Token payload</div>
              <div style={styles.tokenLine}>url: {tokenInfo.url}</div>
              <div style={styles.tokenLine}>room: {tokenInfo.room}</div>
              <div style={styles.tokenLine}>identity: {tokenInfo.identity}</div>
            </div>
          ) : null}
        </section>

        <section style={styles.card}>
          <div style={styles.sectionTitle}>Event log</div>
          <div style={styles.logList}>
            {logs.length ? (
              logs.map((entry, index) => (
                <div key={`${entry.ts}-${index}`} style={styles.logRow}>
                  <span style={styles.logTs}>{entry.ts}</span>
                  <span
                    style={{ ...styles.logLevel, ...levelChipStyle(entry.level) }}
                  >
                    {entry.level.toUpperCase()}
                  </span>
                  <span style={styles.logMessage}>{entry.message}</span>
                </div>
              ))
            ) : (
              <div style={styles.emptyState}>
                Bootstrap a session to see LiveKit and STT events.
              </div>
            )}
          </div>

          <div style={styles.sectionTitle}>What this page verifies</div>
          <ul style={styles.list}>
            <li>Browser microphone permission and capture</li>
            <li>LiveKit token exchange</li>
            <li>Room connection</li>
            <li>Worker dispatch after room exists</li>
            <li>Mic start / pause without destroying the room</li>
            <li>Transcript polling and display</li>
          </ul>
        </section>
      </div>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  page: {
    minHeight: "100vh",
    padding: 24,
    background: "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
  },
  shell: {
    width: "min(1200px, 100%)",
    margin: "0 auto",
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
    gap: 20,
  },
  card: {
    background: "#fff",
    border: "1px solid rgba(15, 23, 42, 0.08)",
    borderRadius: 20,
    boxShadow: "0 16px 40px rgba(15, 23, 42, 0.06)",
    padding: 24,
    display: "grid",
    gap: 16,
  },
  kicker: {
    display: "inline-flex",
    width: "fit-content",
    padding: "6px 10px",
    borderRadius: 999,
    background: "#111827",
    color: "#fff",
    fontSize: 12,
    fontWeight: 700,
  },
  title: {
    margin: 0,
    fontSize: 32,
    lineHeight: 1.1,
    letterSpacing: "-0.03em",
    color: "#0f172a",
  },
  subtext: {
    margin: 0,
    color: "#475569",
    lineHeight: 1.6,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 12,
  },
  field: {
    display: "grid",
    gap: 8,
  },
  label: {
    fontSize: 13,
    fontWeight: 700,
    color: "#334155",
  },
  input: {
    width: "100%",
    borderRadius: 14,
    border: "1px solid rgba(148, 163, 184, 0.28)",
    background: "#f8fafc",
    padding: "12px 14px",
    fontSize: 15,
    outline: "none",
  },
  metrics: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: 12,
  },
  metricCard: {
    background: "#f8fafc",
    border: "1px solid rgba(148, 163, 184, 0.18)",
    borderRadius: 16,
    padding: 16,
  },
  metricLabel: {
    color: "#64748b",
    fontSize: 13,
    marginBottom: 8,
  },
  metricValue: {
    color: "#0f172a",
    fontSize: 20,
    fontWeight: 800,
  },
  transcriptValue: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: 700,
    lineHeight: 1.5,
    minHeight: 54,
    wordBreak: "break-word",
  },
  transcriptStatus: {
    marginTop: 8,
    fontSize: 12,
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    fontWeight: 700,
  },
  buttonRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: 12,
  },
  primaryButton: {
    appearance: "none",
    border: "none",
    borderRadius: 14,
    padding: "12px 18px",
    background: "#111827",
    color: "#fff",
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
  },
  secondaryButton: {
    appearance: "none",
    border: "1px solid rgba(148, 163, 184, 0.4)",
    borderRadius: 14,
    padding: "12px 18px",
    background: "#fff",
    color: "#0f172a",
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
  },
  dangerButton: {
    appearance: "none",
    border: "none",
    borderRadius: 14,
    padding: "12px 18px",
    background: "#b91c1c",
    color: "#fff",
    fontSize: 15,
    fontWeight: 700,
    cursor: "pointer",
  },
  tokenBox: {
    background: "#eff6ff",
    border: "1px solid rgba(37, 99, 235, 0.15)",
    borderRadius: 16,
    padding: 16,
    display: "grid",
    gap: 6,
  },
  tokenTitle: {
    fontWeight: 800,
    color: "#1d4ed8",
    marginBottom: 6,
  },
  tokenLine: {
    fontSize: 13,
    color: "#1e3a8a",
    wordBreak: "break-all",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 800,
    color: "#0f172a",
  },
  logList: {
    display: "grid",
    gap: 10,
    maxHeight: 520,
    overflow: "auto",
  },
  logRow: {
    display: "grid",
    gridTemplateColumns: "88px 76px 1fr",
    gap: 10,
    alignItems: "start",
    padding: "10px 12px",
    borderRadius: 14,
    background: "#f8fafc",
    border: "1px solid rgba(148, 163, 184, 0.18)",
  },
  logTs: {
    fontSize: 12,
    color: "#64748b",
    fontVariantNumeric: "tabular-nums",
  },
  logLevel: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "4px 8px",
    borderRadius: 999,
    fontSize: 11,
    fontWeight: 800,
    letterSpacing: "0.02em",
  },
  logMessage: {
    color: "#0f172a",
    fontSize: 14,
    lineHeight: 1.5,
  },
  emptyState: {
    color: "#64748b",
    fontSize: 14,
    lineHeight: 1.6,
    padding: "10px 2px",
  },
  list: {
    margin: 0,
    paddingLeft: 18,
    display: "grid",
    gap: 8,
    color: "#334155",
    lineHeight: 1.6,
  },
};