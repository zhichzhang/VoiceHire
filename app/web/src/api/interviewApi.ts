import { request } from "./client";

import type {
  BootstrapRequest,
  BootstrapResponse,
  DeleteInterviewResponse,
  InterviewReportResponse,
  InterviewSessionResponse,
  InteractivePhase,
  PhaseTranscriptRequest,
  ResumeRequest,
  WorkflowResult,
} from "../types/api";

export function bootstrapInterview(
  payload: BootstrapRequest,
): Promise<BootstrapResponse> {
  return request<BootstrapResponse>("/interview/bootstrap", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resumeInterview(
  payload: ResumeRequest,
): Promise<InterviewSessionResponse> {
  return request<InterviewSessionResponse>("/interview/resume", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getInterviewSession(
  sessionId: string,
): Promise<InterviewSessionResponse> {
  return request<InterviewSessionResponse>(`/interview/sessions/${sessionId}`);
}

export function getInterviewReport(
  sessionId: string,
): Promise<InterviewReportResponse> {
  return request<InterviewReportResponse>(`/interview/sessions/${sessionId}/report`);
}

export function submitPhaseTranscript(
  sessionId: string,
  phase: InteractivePhase,
  payload: PhaseTranscriptRequest,
): Promise<WorkflowResult> {
  return request<WorkflowResult>(
    `/interview/sessions/${sessionId}/phases/${phase}/transcript`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function finalizeInterview(
  sessionId: string,
): Promise<WorkflowResult> {
  return request<WorkflowResult>(`/interview/sessions/${sessionId}/evaluation`, {
    method: "POST",
  });
}

export function deleteInterviewSession(
  sessionId: string,
): Promise<DeleteInterviewResponse> {
  return request<DeleteInterviewResponse>(`/interview/sessions/${sessionId}`, {
    method: "DELETE",
  });
}
