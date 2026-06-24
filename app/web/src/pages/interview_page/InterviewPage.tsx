import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  deleteInterviewSession,
  finalizeInterview,
  getInterviewSession,
  submitPhaseTranscript,
} from "../../api/interviewApi";
import { useInterviewStore } from "../../store/interviewStore";
import type { InterviewSession } from "../../types/api";
import {
  buttonStyle,
  cardStyle,
  countdownHeroStyle,
  countdownHintStyle,
  countdownLabelStyle,
  countdownValueStyle,
  disabledButtonStyle,
  errorStyle,
  helperTextStyle,
  layoutStyle,
  pageStyle,
  primaryChipStyle,
  questionStyle,
  readingProgressBarStyle,
  readingProgressStyle,
  statusPillStyle,
} from "./InterviewPage.syles";

import { InterviewAnswerRecorder } from "../../components/interview/InterviewAnswerRecorder";
import { useLiveKitAnswerRecorder } from "../../hooks/useLiveKitAnswerRecorder";

type InteractivePhase = "intro" | "experience";

type InterviewMode =
  | "loading"
  | "viewing_question"
  | "answering"
  | "awaiting_transcript"
  | "submitting"
  | "completed";

type WorkflowResult = {
  kind:
    | "question"
    | "phase_completed"
    | "final_report"
    | "ack"
    | "ignored"
    | "error";
  phase?: string | null;
  text?: string | null;
  time_limit_seconds?: number | null;
  evaluation?: unknown;
  session?: InterviewSession | null;
  error?: string | null;
};

const DEFAULT_QUESTION_VIEW_SECONDS = 30;
const DEFAULT_ANSWER_SECONDS = 90;

function toInteractivePhase(
  value: string | null | undefined,
): InteractivePhase | null {
  if (value === "intro" || value === "experience") {
    return value;
  }
  return null;
}

function formatSeconds(totalSeconds: number): string {
  const safe = Math.max(0, totalSeconds);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function phaseLabel(phase: string | null | undefined): string {
  if (phase === "intro") return "Intro";
  if (phase === "experience") return "Experience";
  if (phase === "evaluation") return "Evaluation";
  if (phase === "completed") return "Completed";
  return phase ?? "—";
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function resolveTimings(session: InterviewSession): {
  readingSeconds: number;
  answerSeconds: number;
} {
  const s = session as InterviewSession & {
    current_question_time_limit_seconds?: number;
    question_time_limit_seconds?: number;
    reading_time_limit_seconds?: number;
    current_answer_time_limit_seconds?: number;
    answer_time_limit_seconds?: number;
  };

  return {
    readingSeconds:
      s.current_question_time_limit_seconds ??
      s.question_time_limit_seconds ??
      s.reading_time_limit_seconds ??
      DEFAULT_QUESTION_VIEW_SECONDS,
    answerSeconds:
      s.current_answer_time_limit_seconds ??
      s.answer_time_limit_seconds ??
      DEFAULT_ANSWER_SECONDS,
  };
}

function buildInteractiveTurnState(session: InterviewSession) {
  const { readingSeconds, answerSeconds } = resolveTimings(session);
  const now = Date.now();

  return {
    questionViewSeconds: readingSeconds,
    answerSeconds,
    questionDeadline: now + readingSeconds * 1000,
    answerDeadline: null as number | null,
    now,
  };
}

export default function InterviewPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const phase = useInterviewStore((s) => s.phase);
  const cachedSession = useInterviewStore((s) => s.currentSession);
  const currentQuestion = useInterviewStore((s) => s.currentQuestion);
  const storedSessionId = useInterviewStore((s) => s.sessionId);
  const storeError = useInterviewStore((s) => s.error);

  const setSessionState = useInterviewStore((s) => s.setSessionState);
  const setLatestTranscript = useInterviewStore((s) => s.setLatestTranscript);
  const setError = useInterviewStore((s) => s.setError);
  const clearStore = useInterviewStore((s) => s.clear);

  const [pageError, setPageError] = useState<string | null>(null);
  const [mode, setMode] = useState<InterviewMode>("loading");
  const [questionDeadline, setQuestionDeadline] = useState<number | null>(null);
  const [answerDeadline, setAnswerDeadline] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [isEnding, setIsEnding] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [questionViewSeconds, setQuestionViewSeconds] = useState(
    DEFAULT_QUESTION_VIEW_SECONDS,
  );
  const [answerSeconds, setAnswerSeconds] = useState(DEFAULT_ANSWER_SECONDS);

  const activeSessionId = sessionId ?? storedSessionId;

  const recorder = useLiveKitAnswerRecorder({
    sessionId: activeSessionId,
    autoConnect: false,
    pollIntervalMs: 500,
  });

  const {
    connected,
    status: recorderStatus,
    micEnabled,
    audioLevel,
    participantCount,
    roomName,
    identity,
    transcript,
    latestIsFinal,
    connect: connectRecorder,
    startRecording,
    stopRecording,
    disconnect: disconnectRecorder,
    clearTranscript,
    error: recorderError,
  } = recorder;

  const questionCountdown =
    questionDeadline === null
      ? questionViewSeconds
      : Math.max(0, Math.ceil((questionDeadline - now) / 1000));

  const answerCountdown =
    answerDeadline === null
      ? answerSeconds
      : Math.max(0, Math.ceil((answerDeadline - now) / 1000));

  const questionText = currentQuestion || "Waiting for the next question...";
  const inlineError = pageError ?? storeError ?? recorderError ?? null;

  const readingProgress = useMemo(() => {
    if (questionViewSeconds <= 0) return 0;
    const ratio = 1 - questionCountdown / questionViewSeconds;
    return Math.max(0, Math.min(1, ratio));
  }, [questionCountdown, questionViewSeconds]);

  const modeLabel = useMemo(() => {
    if (mode === "viewing_question") {
      return `Reading ${formatSeconds(questionCountdown)}`;
    }
    if (mode === "answering") {
      return `Answering ${formatSeconds(answerCountdown)}`;
    }
    if (mode === "awaiting_transcript") {
      return "Waiting for final transcript";
    }
    if (mode === "submitting") {
      return "Uploading answer";
    }
    if (mode === "completed") {
      return "Completed";
    }
    return "Initializing";
  }, [answerCountdown, mode, questionCountdown]);

  const statusToneStyle = useMemo(() => {
    if (mode === "answering") {
      return { background: "#ecfdf5", color: "#065f46" };
    }
    if (mode === "awaiting_transcript" || mode === "submitting") {
      return { background: "#fff7ed", color: "#9a3412" };
    }
    if (mode === "completed") {
      return { background: "#eef2ff", color: "#3730a3" };
    }
    return { background: "#eff6ff", color: "#1d4ed8" };
  }, [mode]);

  const bootstrapInteractiveTurn = useCallback(
    (session: InterviewSession) => {
      const next = buildInteractiveTurnState(session);

      setQuestionViewSeconds(next.questionViewSeconds);
      setAnswerSeconds(next.answerSeconds);
      setLatestTranscript("", false);
      clearTranscript();
      setMode("viewing_question");
      setQuestionDeadline(next.questionDeadline);
      setAnswerDeadline(next.answerDeadline);
      setNow(next.now);
    },
    [clearTranscript, setLatestTranscript],
  );

  const startAnswering = useCallback(async () => {
    if (!sessionId) return;

    const currentPhase = toInteractivePhase(phase);
    if (!currentPhase) return;

    setMode("answering");
    setQuestionDeadline(null);
    setAnswerDeadline(Date.now() + answerSeconds * 1000);
    setNow(Date.now());
    setLatestTranscript("", false);
    clearTranscript();

    try {
      await startRecording();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to start recording";

      setError(message);
      setMode("viewing_question");
      setQuestionDeadline(Date.now() + questionViewSeconds * 1000);
      setAnswerDeadline(null);
    }
  }, [
    answerSeconds,
    clearTranscript,
    phase,
    questionViewSeconds,
    sessionId,
    setError,
    setLatestTranscript,
    startRecording,
  ]);

  const submitCurrentAnswer = useCallback(
    async (transcriptText: string) => {
      if (!sessionId) {
        throw new Error("Missing session id.");
      }

      const activePhase = toInteractivePhase(phase);
      if (!activePhase) {
        throw new Error(
          "Transcript can only be submitted for intro or experience.",
        );
      }

      try {
        const workflow = (await submitPhaseTranscript(
          sessionId,
          activePhase,
          { text: transcriptText },
        )) as WorkflowResult;

        if (workflow.kind === "error") {
          throw new Error(workflow.error || "Failed to submit transcript");
        }

        const refreshedSession =
          workflow.session ?? (await getInterviewSession(sessionId)).session;

        setSessionState(refreshedSession);

        if (
          workflow.kind === "phase_completed" ||
          workflow.kind === "final_report"
        ) {
          for (let attempt = 0; attempt < 20; attempt += 1) {
            try {
              await finalizeInterview(sessionId);
              navigate(
                `/session/${sessionId}/loading?next=evaluation&restore=0`,
                { replace: true },
              );
              return;
            } catch (err) {
              const message = err instanceof Error ? err.message : "";
              if (!message.includes("Turn assessments are still processing")) {
                throw err;
              }
              await sleep(1000);
            }
          }

          throw new Error("Turn assessments are still processing.");
        }

        const nextPhase = toInteractivePhase(refreshedSession.current_phase);

        if (nextPhase) {
          navigate(`/session/${sessionId}/loading?next=interview&restore=0`, {
            replace: true,
          });
          return;
        }

        navigate(`/session/${sessionId}/loading?next=evaluation&restore=0`, {
          replace: true,
        });
      } finally {
        // no-op
      }
    },
    [navigate, phase, sessionId, setSessionState],
  );

  const handleStopAnswering = useCallback(async () => {
    if (!sessionId) return;
    if (mode !== "answering" || isSubmitting || isEnding) return;

    setMode("awaiting_transcript");
    setAnswerDeadline(null);
    setError(null);

    try {
      const transcriptText = await stopRecording();
      const cleanedTranscript = transcriptText.trim();

      setLatestTranscript(cleanedTranscript, true);

      setMode("submitting");
      setIsSubmitting(true);

      await submitCurrentAnswer(cleanedTranscript);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to submit transcript";

      setError(message);
      setMode("answering");
      setAnswerDeadline(Date.now() + answerSeconds * 1000);

      try {
        await startRecording();
      } catch {
        // best effort
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [
    answerSeconds,
    isEnding,
    isSubmitting,
    mode,
    sessionId,
    setError,
    setLatestTranscript,
    startRecording,
    stopRecording,
    submitCurrentAnswer,
  ]);

  const handleAbortInterview = useCallback(async () => {
    if (!sessionId || isEnding) return;

    setIsEnding(true);

    try {
      await Promise.allSettled([
        disconnectRecorder(),
        deleteInterviewSession(sessionId),
      ]);
    } finally {
      clearStore();
      navigate("/", { replace: true });
    }
  }, [clearStore, disconnectRecorder, isEnding, navigate, sessionId]);

  const turnKey = `${sessionId}:${phase}:${currentQuestion}`;
  const hasAutoStartedRef = useRef(false);
  const bootstrappedSessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    hasAutoStartedRef.current = false;
  }, [turnKey]);

  useEffect(() => {
    if (mode !== "viewing_question") return;
    if (questionCountdown > 0) return;
    if (hasAutoStartedRef.current) return;

    hasAutoStartedRef.current = true;
    void startAnswering();
  }, [mode, questionCountdown, startAnswering]);

  useEffect(() => {
    setLatestTranscript(transcript.trim(), latestIsFinal);
  }, [latestIsFinal, setLatestTranscript, transcript]);

  useEffect(() => {
    if (!sessionId) return;
    if (bootstrappedSessionIdRef.current === sessionId) return;

    let cancelled = false;

    const load = async () => {
      try {
        setPageError(null);

        const reusableSession =
          cachedSession?.session_id === sessionId ? cachedSession : null;

        const nextSession =
          reusableSession ?? (await getInterviewSession(sessionId)).session;

        if (cancelled) return;

        const nextPhase = toInteractivePhase(nextSession.current_phase);

        if (!nextPhase) {
          bootstrappedSessionIdRef.current = sessionId;
          setSessionState(nextSession);
          setMode("completed");
          navigate(`/session/${sessionId}/loading?next=evaluation&restore=0`, {
            replace: true,
          });
          return;
        }

        bootstrappedSessionIdRef.current = sessionId;
        setSessionState(nextSession);
        bootstrapInteractiveTurn(nextSession);

        if (cancelled) return;

        void connectRecorder();
      } catch (err) {
        if (!cancelled) {
          bootstrappedSessionIdRef.current = null;
          const message =
            err instanceof Error ? err.message : "Failed to load interview";
          setPageError(message);
          setError(message);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [
    bootstrapInteractiveTurn,
    cachedSession,
    connectRecorder,
    navigate,
    sessionId,
    setError,
    setSessionState,
  ]);

  useEffect(() => {
    const timerId = window.setInterval(() => {
      setNow(Date.now());
    }, 500);

    return () => {
      window.clearInterval(timerId);
    };
  }, []);

  useEffect(() => {
    if (mode !== "viewing_question") return;
    if (questionCountdown > 0) return;
    if (hasAutoStartedRef.current) return;

    hasAutoStartedRef.current = true;

    const timerId = window.setTimeout(() => {
      void startAnswering();
    }, 0);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [mode, questionCountdown, startAnswering]);

  useEffect(() => {
    if (mode !== "answering") {
      return;
    }

    if (answerCountdown > 0) {
      return;
    }

    const timerId = window.setTimeout(() => {
      void handleStopAnswering();
    }, 0);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [answerCountdown, handleStopAnswering, mode]);

  if (!sessionId) {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Missing session id</h2>
          <p style={helperTextStyle}>
            The interview page needs a session id in the route.
          </p>
          <button
            type="button"
            style={buttonStyle}
            onClick={() => navigate("/")}
          >
            Back to landing
          </button>
        </div>
      </div>
    );
  }

  if (pageError) {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Unable to load interview</h2>
          <p style={errorStyle}>{pageError}</p>
          <button
            type="button"
            style={buttonStyle}
            onClick={() => navigate("/")}
          >
            Back to landing
          </button>
        </div>
      </div>
    );
  }

  const nextDisabled =
    mode !== "answering" || isSubmitting || isEnding || !connected;

  return (
    <div style={pageStyle}>
      <div style={layoutStyle}>
        <section style={cardStyle}>
          <h2 style={{ marginTop: 0 }}>Question</h2>

          <div style={statusPillStyle}>
            <span>Phase: {phaseLabel(phase)}</span>
            <span style={statusToneStyle as React.CSSProperties}>
              {modeLabel}
            </span>
            <span>Session: {sessionId}</span>
          </div>

          {mode === "viewing_question" && (
            <div style={countdownHeroStyle}>
              <div style={countdownLabelStyle}>Reading Time</div>
              <div style={countdownValueStyle}>
                {formatSeconds(questionCountdown)}
              </div>
              <div style={countdownHintStyle}>
                Recording will begin automatically when this reaches zero.
              </div>
              <div style={readingProgressStyle}>
                <div
                  style={{
                    ...readingProgressBarStyle,
                    width: `${Math.round(readingProgress * 100)}%`,
                  }}
                />
              </div>
            </div>
          )}

          {mode === "answering" && (
            <div
              style={{
                ...countdownHeroStyle,
                background: "#ecfdf5",
                border: "1px solid rgba(16, 185, 129, 0.18)",
              }}
            >
              <div
                style={{
                  ...countdownLabelStyle,
                  color: "#047857",
                }}
              >
                Answer Time
              </div>
              <div
                style={{
                  ...countdownValueStyle,
                  color: "#047857",
                }}
              >
                {formatSeconds(answerCountdown)}
              </div>
              <div style={countdownHintStyle}>
                Your answer is being recorded.
              </div>
            </div>
          )}

          <div style={questionStyle}>{questionText}</div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <button
              type="button"
              style={{
                ...buttonStyle,
                ...(nextDisabled ? disabledButtonStyle : null),
              }}
              disabled={nextDisabled}
              onClick={() => void handleStopAnswering()}
            >
              Next
            </button>

            <button
              type="button"
              style={{
                ...buttonStyle,
                background: "#b91c1c",
                ...(isEnding ? disabledButtonStyle : null),
              }}
              disabled={isEnding}
              onClick={() => void handleAbortInterview()}
            >
              End Interview
            </button>
          </div>

          <p style={helperTextStyle}>
            {`${questionViewSeconds} seconds of reading starts the answer recording automatically. When the ${answerSeconds} second answer window ends, the page pauses recording, sends the transcript to the server, and advances to the next turn.`}
          </p>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <span style={primaryChipStyle}>Recorder: {recorderStatus}</span>
            <span style={primaryChipStyle}>Room: {roomName || "—"}</span>
            <span style={primaryChipStyle}>Identity: {identity || "—"}</span>
            <span style={primaryChipStyle}>
              Participants: {participantCount}
            </span>
            <span style={primaryChipStyle}>Connected: {String(connected)}</span>
            <span style={primaryChipStyle}>Mic: {String(micEnabled)}</span>
          </div>

          {inlineError ? <p style={errorStyle}>{inlineError}</p> : null}
        </section>

        <InterviewAnswerRecorder
          title="Live transcript"
          transcript={transcript}
          isFinal={latestIsFinal}
          audioLevel={audioLevel}
          micEnabled={micEnabled}
          statusText={
            mode === "viewing_question"
              ? `Reading question ${formatSeconds(questionCountdown)}`
              : mode === "answering"
                ? `Recording answer ${formatSeconds(answerCountdown)}`
                : mode === "awaiting_transcript"
                  ? "Waiting for final transcript"
                  : mode === "submitting"
                    ? "Submitting answer"
                    : mode === "completed"
                      ? "Completed"
                      : "Initializing"
          }
          placeholder="Waiting for speech..."
        />
      </div>
    </div>
  );
}