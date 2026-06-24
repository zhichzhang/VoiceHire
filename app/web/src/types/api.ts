// app/web/src/types/api.ts

// ============================================================
// Shared phases / statuses
// ============================================================

export type InteractivePhase = "intro" | "experience";
export type InterviewFlowPhase = "intro" | "experience" | "evaluation" | "completed";

export type SessionStatus = "active" | "processing" | "completed" | "expired" | "failed" | string;
export type AssessmentStatus = "pending" | "processing" | "completed" | "failed" | string;

export interface BootstrapRecord {
  id?: string;
  name?: string;
  email?: string;
  [key: string]: unknown;
}

// ============================================================
// Resume models
// ============================================================

export interface ResumeEducation {
  institution: string;
  program?: string | null;
  timeframe?: string | null;
  status?: string | null;
}

export interface ResumeExperience {
  name: string;
  organization?: string | null;
  experience_type?: string | null;
  timeframe?: string | null;
  summary: string;
  skills: string[];
}

export interface CandidateResume {
  education: ResumeEducation[];
  experiences: ResumeExperience[];
  skills: string[];
}

// ============================================================
// Candidate profile models
// ============================================================

export interface EducationContext {
  institution: string;
  program?: string | null;
  status?: string | null;
}

export interface HighlightedExperience {
  organization?: string | null;
  timeframe?: string | null;
  summary: string;
  responsibilities: string[];
  achievements: string[];
}

export interface CandidateProfile {
  most_recent_role?: string | null;
  education?: EducationContext | null;
  highlighted_experiences: HighlightedExperience[];
  domain_keywords: string[];
  other_context: string[];
}

// ============================================================
// Experience evidence
// ============================================================

export interface ExperienceEvidence {
  experience_type?: string | null;
  experience_name?: string | null;
  what?: string | null;
  why?: string | null;
  how?: string | null;
  challenge?: string | null;
  outcome?: string | null;
}

// ============================================================
// Turn assessment / interview turn
// ============================================================

export interface TurnAssessment {
  relevance: number;
  clarity: number;
  fluency: number;
}

export interface InterviewTurn {
  turn_number?: number | null;
  phase: string;
  question: string;
  answer: string;
  assessment: TurnAssessment;
  assessment_status: AssessmentStatus;
  assessment_error?: string | null;
  assessed_at?: string | null;
}

// ============================================================
// Interview feedback / evaluation
// ============================================================

export interface Recommendation {
  category:
    | "communication"
    | "ownership"
    | "problem_solving"
    | "impact"
    | "domain_expertise"
    | string;
  priority: "high" | "medium" | "low" | string;
  recommendation: string;
}

export interface LLMInterviewFeedback {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: Recommendation[];
}

export interface CommunicationMetrics {
  relevance: number;
  clarity: number;
  fluency: number;
}

export interface DimensionScore {
  name: string;
  score: number;
  justification: string;
}

export interface PhaseEvaluation {
  phase_name: string;
  dimensions: DimensionScore[];
  overall_score: number;
  strengths: string[];
  improvements: string[];
}

export interface InterviewEvaluation {
  phase_results: PhaseEvaluation[];
  communication_metrics: CommunicationMetrics;
  communication_score: number;
  professional_score: number;
  overall_score: number;
  assessment_confidence: number;
  llm_feedback?: LLMInterviewFeedback | null;
}

// ============================================================
// Interview session
// ============================================================

export interface InterviewSession {
  session_id: string;
  current_phase: string;
  status: SessionStatus;
  current_question?: string | null;
  current_answer?: string | null;
  turns: InterviewTurn[];
  candidate_profile: CandidateProfile;
  experience_evidence: ExperienceEvidence;
  evaluation?: InterviewEvaluation | null;
  resume_context?: CandidateResume | null;
  started_at?: string | null;
  completed_at?: string | null;
  expires_at?: string | null;
}

// ============================================================
// Bootstrap / resume / report
// ============================================================

export interface BootstrapRequest {
  email: string;
  name: string;
  raw_resume_text?: string | null;
}

export interface ResumeRequest {
  session_id?: string | null;
}

export interface BootstrapResponse {
  candidate: BootstrapRecord;
  resume: BootstrapRecord;
  normalized_resume: CandidateResume;
  is_new_candidate: boolean;
  resume_updated: boolean;
  used_existing_resume: boolean;
  session: InterviewSession;
  first_question: {
    text: string;
    time_limit_seconds: number;
  };
}

export interface InterviewSessionResponse {
  candidate: BootstrapRecord;
  resume: BootstrapRecord;
  session: InterviewSession;
}

export interface InterviewReportResponse {
  session: InterviewSession;
  evaluation: InterviewEvaluation | null;
  turns: InterviewTurn[];
}

export interface WorkflowResult {
  kind: "question" | "phase_completed" | "final_report" | "ack" | "ignored" | "error";
  phase?: string | null;
  text?: string | null;
  time_limit_seconds?: number | null;
  evaluation?: InterviewEvaluation | null;
  session?: InterviewSession | null;
  error?: string | null;
}

// ============================================================
// Transcript submit
// ============================================================

export interface PhaseTranscriptRequest {
  text: string;
}

// ============================================================
// Transcribe models
// ============================================================

/**
 * Request body for creating a LiveKit token.
 */
export interface TranscribeTokenRequest {
  session_id: string;
}

/**
 * LiveKit token response returned to the browser.
 */
export interface LiveKitTokenResponse {
  url: string;
  room: string;
  identity: string;
  token: string;
}

/**
 * Request body for starting a transcription session.
 *
 * The simplified STT flow no longer tracks phase on the
 * transcription API side.
 */
export interface StartTranscriptionRequest {
  session_id: string;
  reset?: boolean;
}

/**
 * Request body for storing one transcript chunk.
 *
 * The simplified STT flow only stores the text and whether
 * it is final.
 */
export interface TranscriptChunkRequest {
  text: string;
  is_final?: boolean;
}

/**
 * Request body for finalizing a transcription session.
 */
export interface FinalizeTranscriptionRequest {
  session_id: string;
}

/**
 * One stored transcript chunk.
 */
export interface TranscriptChunk {
  chunk_id: string;
  text: string;
  is_final: boolean;
  created_at: string;
}

/**
 * Runtime transcription session state.
 */
export interface TranscriptionSessionState {
  session_id: string;
  active: boolean;
  latest_text: string;
  latest_is_final: boolean;
  updated_at: string;
  chunks: TranscriptChunk[];
}

export interface TranscriptionSessionResponse {
  session: TranscriptionSessionState;
}

/**
 * Lightweight payload returned to the frontend polling loop.
 */
export interface LatestTranscriptResponse {
  session_id: string;
  text: string;
  is_final: boolean;
  active: boolean;
  updated_at: string;
  chunk_count: number;
}

export interface DeleteTranscriptionResponse {
  deleted: boolean;
  session_id: string;
}

export interface DeleteInterviewResponse {
  deleted: boolean;
  session_id: string;
}

export interface TranscriptChunk {
  chunk_id: string;
  text: string;
  is_final: boolean;
  created_at: string;
}

export interface ParsedTranscriptResponse {
  session_id: string;
  active: boolean;
  latest_text: string;
  latest_is_final: boolean;
  final_text: string;
  parsed_text: string;
  chunk_count: number;
  final_chunk_count: number;
  final_chunks: TranscriptChunk[];
  updated_at: string;
}

export interface DispatchTranscriptionResponse {
  ok: boolean;
  room: string;
  agent_name: string;
  dispatch_id: string;
  already_dispatched: boolean;
}

