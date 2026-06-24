import { request } from "./client";

import type {
  DispatchTranscriptionResponse,
  FinalizeTranscriptionRequest,
  LatestTranscriptResponse,
  ParsedTranscriptResponse,
  StartTranscriptionRequest,
  TranscribeTokenRequest,
  TranscriptionSessionResponse,
  DeleteTranscriptionResponse,
} from "../types/api";

export function createTranscribeToken(
  sessionId: string,
): Promise<{ url: string; room: string; identity: string; token: string }> {
  return request(`/transcribe/token`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId } satisfies TranscribeTokenRequest),
  });
}

export function dispatchTranscriptionWorker(
  sessionId: string,
): Promise<DispatchTranscriptionResponse> {
  return request<DispatchTranscriptionResponse>(
    `/transcribe/sessions/${sessionId}/dispatch`,
    {
      method: "POST",
    },
  );
}

export function startTranscriptionSession(
  payload: StartTranscriptionRequest,
): Promise<TranscriptionSessionResponse> {
  return request<TranscriptionSessionResponse>(
    `/transcribe/sessions/${payload.session_id}/start`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function finalizeTranscriptionSession(
  sessionId: string,
): Promise<TranscriptionSessionResponse> {
  return request<TranscriptionSessionResponse>(
    `/transcribe/sessions/${sessionId}/finalize`,
    {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId } satisfies FinalizeTranscriptionRequest),
    },
  );
}

export function deleteTranscriptionSession(
  sessionId: string,
): Promise<DeleteTranscriptionResponse> {
  return request<DeleteTranscriptionResponse>(
    `/transcribe/sessions/${sessionId}`,
    {
      method: "DELETE",
    },
  );
}

export function clearTranscriptionSession(
  sessionId: string,
): Promise<TranscriptionSessionResponse> {
  return request<TranscriptionSessionResponse>(
    `/transcribe/sessions/${sessionId}/clear`,
    {
      method: "POST",
    },
  );
}

export function getLatestTranscript(
  sessionId: string,
): Promise<LatestTranscriptResponse> {
  return request<LatestTranscriptResponse>(
    `/transcribe/sessions/${sessionId}/latest`,
  );
}

export function getParsedTranscript(
  sessionId: string,
): Promise<ParsedTranscriptResponse> {
  return request<ParsedTranscriptResponse>(
    `/transcribe/sessions/${sessionId}/result`,
  );
}
