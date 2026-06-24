// app/web/src/store/interviewStore.ts

import { create } from "zustand";
import type {
  BootstrapResponse,
  InterviewFlowPhase,
  InterviewSession,
  SessionStatus,
} from "../types/api";

interface InterviewStore {
  sessionId: string | null;
  phase: InterviewFlowPhase;
  status: SessionStatus;
  candidateName: string;
  candidateEmail: string;
  resumeText: string;
  firstQuestion: string;
  firstQuestionTimeLimitSeconds: number;
  currentQuestion: string;
  currentSession: InterviewSession | null;   // 新增
  latestTranscript: string;
  latestTranscriptIsFinal: boolean;
  isLoading: boolean;
  error: string | null;

  setBootstrapState: (
    payload: BootstrapResponse,
    resumeText?: string,
  ) => void;
  setSessionState: (session: InterviewSession) => void;
  setLatestTranscript: (text: string, isFinal: boolean) => void;
  setLoading: (value: boolean) => void;
  setError: (value: string | null) => void;
  clear: () => void;
}

const initialState = {
  sessionId: null,
  phase: "intro" as InterviewFlowPhase,
  status: "idle",
  candidateName: "",
  candidateEmail: "",
  resumeText: "",
  firstQuestion: "",
  firstQuestionTimeLimitSeconds: 0,
  currentQuestion: "",
  currentSession: null,
  latestTranscript: "",
  latestTranscriptIsFinal: false,
  isLoading: false,
  error: null,
};

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

export const useInterviewStore = create<InterviewStore>((set) => ({
  ...initialState,

  setBootstrapState: (payload, resumeText = "") =>
  set({
    sessionId: payload.session.session_id,
    phase: (payload.session.current_phase as InterviewFlowPhase) ?? "intro",
    status: payload.session.status ?? "active",
    candidateName: readString(payload.candidate.name),
    candidateEmail: readString(payload.candidate.email),
    resumeText,
    firstQuestion: payload.first_question.text,
    firstQuestionTimeLimitSeconds: payload.first_question.time_limit_seconds,
    currentQuestion:
      readString(payload.session.current_question, payload.first_question.text) ||
      payload.first_question.text,
    currentSession: payload.session,
    error: null,
  }),

setSessionState: (session) =>
  set((state) => ({
    sessionId: session.session_id,
    phase: (session.current_phase as InterviewFlowPhase) ?? state.phase,
    status: session.status ?? state.status,
    currentQuestion:
      (session.current_question as string | null | undefined) ??
      state.currentQuestion,
    currentSession: session,
    error: null,
  })),

  setLatestTranscript: (text, isFinal) =>
    set({
      latestTranscript: text,
      latestTranscriptIsFinal: isFinal,
    }),

  setLoading: (value) => set({ isLoading: value }),
  setError: (value) => set({ error: value }),

  clear: () => set({ ...initialState }),
}));