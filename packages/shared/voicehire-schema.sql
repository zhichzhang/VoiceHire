-- ============================================================
-- VoiceHire Database Schema
-- ============================================================
--
-- This schema persists:
--   - Candidate information
--   - Resume context
--   - Interview sessions
--   - Interview turns
--   - Extracted interview evidence
--   - Final interview evaluations
--
-- Most LLM-generated artifacts are stored as JSONB to support
-- schema evolution and minimize migration overhead.
--
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: candidates
-- ============================================================
--
-- Core candidate entity.
--
-- Stores persistent candidate information.
--
-- A candidate may participate in multiple interview sessions.
--
-- ============================================================

CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE candidates IS 'Persistent candidate information.';
COMMENT ON COLUMN candidates.id IS 'Unique candidate identifier.';
COMMENT ON COLUMN candidates.email IS 'Candidate email address.';
COMMENT ON COLUMN candidates.name IS 'Candidate display name.';
COMMENT ON COLUMN candidates.created_at IS 'Record creation timestamp.';
COMMENT ON COLUMN candidates.updated_at IS 'Record last update timestamp.';

-- ============================================================
-- TABLE: candidate_resumes
-- ============================================================
--
-- Stores structured resume data.
--
-- Resume data is treated as system context and loaded before
-- an interview session begins.
--
-- The resume JSON mirrors the CandidateResume model.
--
-- ============================================================

CREATE TABLE candidate_resumes (
    candidate_id UUID PRIMARY KEY REFERENCES candidates(id) ON DELETE CASCADE,
    resume_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE candidate_resumes IS 'Structured resume information associated with a candidate.';
COMMENT ON COLUMN candidate_resumes.candidate_id IS 'Candidate owning the resume.';
COMMENT ON COLUMN candidate_resumes.resume_json IS 'Serialized CandidateResume model.';
COMMENT ON COLUMN candidate_resumes.created_at IS 'Resume creation timestamp.';
COMMENT ON COLUMN candidate_resumes.updated_at IS 'Resume last update timestamp.';

CREATE INDEX idx_candidate_resumes_resume_json
ON candidate_resumes
USING GIN (resume_json);

-- ============================================================
-- TABLE: interview_sessions
-- ============================================================
--
-- Represents a single interview attempt.
--
-- A session owns:
--   - Interview turns
--   - Candidate profile state
--   - Experience evidence
--   - Final evaluation
--
-- Resume / recovery support:
--   - Pending question
--   - Pending answer
--   - Session expiration
--
-- ============================================================

CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    current_phase TEXT NOT NULL,
    status TEXT NOT NULL,
    current_question TEXT,
    current_answer TEXT,
    expires_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE interview_sessions IS 'Top-level interview runtime entity.';
COMMENT ON COLUMN interview_sessions.id IS 'Unique interview session identifier.';
COMMENT ON COLUMN interview_sessions.candidate_id IS 'Candidate associated with this interview.';
COMMENT ON COLUMN interview_sessions.current_phase IS 'Current workflow phase.';
COMMENT ON COLUMN interview_sessions.status IS 'Session status such as active, processing, completed, expired, or failed.';
COMMENT ON COLUMN interview_sessions.current_question IS 'Most recently generated question awaiting an answer.';
COMMENT ON COLUMN interview_sessions.current_answer IS 'Most recently submitted answer that is still being processed.';
COMMENT ON COLUMN interview_sessions.expires_at IS 'Session expiration timestamp used for resume and cleanup.';
COMMENT ON COLUMN interview_sessions.started_at IS 'Interview start timestamp.';
COMMENT ON COLUMN interview_sessions.completed_at IS 'Interview completion timestamp.';

CREATE INDEX idx_interview_sessions_candidate_id
ON interview_sessions(candidate_id);

CREATE INDEX idx_interview_sessions_status
ON interview_sessions(status);

CREATE INDEX idx_interview_sessions_started_at
ON interview_sessions(started_at DESC);

-- ============================================================
-- TABLE: interview_turns
-- ============================================================
--
-- Stores every interviewer-candidate interaction.
--
-- turn_number preserves deterministic ordering and should
-- always be used when replaying conversations.
--
-- ============================================================

CREATE TABLE interview_turns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    phase TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,

    relevance DOUBLE PRECISION,
    clarity DOUBLE PRECISION,
    fluency DOUBLE PRECISION,

    assessment_status TEXT NOT NULL DEFAULT 'pending',
    assessment_error TEXT,
    assessed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (session_id, turn_number)
);

COMMENT ON TABLE interview_turns IS 'Interview conversation history.';
COMMENT ON COLUMN interview_turns.id IS 'Unique interview turn identifier.';
COMMENT ON COLUMN interview_turns.session_id IS 'Owning interview session.';
COMMENT ON COLUMN interview_turns.turn_number IS 'Sequential turn number within a session.';
COMMENT ON COLUMN interview_turns.phase IS 'Interview phase during which the turn occurred.';
COMMENT ON COLUMN interview_turns.question IS 'Question presented to the candidate.';
COMMENT ON COLUMN interview_turns.answer IS 'Candidate response.';
COMMENT ON COLUMN interview_turns.relevance IS 'Relevance score assigned to the answer.';
COMMENT ON COLUMN interview_turns.clarity IS 'Clarity score assigned to the answer.';
COMMENT ON COLUMN interview_turns.fluency IS 'Fluency score assigned to the answer.';
COMMENT ON COLUMN interview_turns.assessment_status IS 'Turn assessment status: pending, processing, completed, or failed.';
COMMENT ON COLUMN interview_turns.assessment_error IS 'Assessment error message when turn scoring fails.';
COMMENT ON COLUMN interview_turns.assessed_at IS 'Timestamp when turn assessment was completed or failed.';
COMMENT ON COLUMN interview_turns.created_at IS 'Turn creation timestamp.';

CREATE INDEX idx_interview_turns_session_id
ON interview_turns(session_id);

CREATE INDEX idx_interview_turns_session_turn
ON interview_turns(session_id, turn_number);

CREATE INDEX idx_interview_turns_assessment_status
ON interview_turns(assessment_status);

CREATE INDEX idx_interview_turns_session_assessment_status
ON interview_turns(session_id, assessment_status);

-- ============================================================
-- TABLE: session_profiles
-- ============================================================
--
-- Stores the current CandidateProfile snapshot.
--
-- This represents interview-discovered context rather than
-- resume information.
--
-- ============================================================

CREATE TABLE session_profiles (
    session_id UUID PRIMARY KEY REFERENCES interview_sessions(id) ON DELETE CASCADE,
    profile_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE session_profiles IS 'Serialized CandidateProfile state.';
COMMENT ON COLUMN session_profiles.session_id IS 'Associated interview session.';
COMMENT ON COLUMN session_profiles.profile_json IS 'Serialized CandidateProfile model.';
COMMENT ON COLUMN session_profiles.updated_at IS 'Profile last update timestamp.';

CREATE INDEX idx_session_profiles_json
ON session_profiles
USING GIN (profile_json);

-- ============================================================
-- TABLE: session_experience_evidence
-- ============================================================
--
-- Stores structured experience evidence collected during
-- the experience phase.
--
-- The JSON payload mirrors the ExperienceEvidence model.
--
-- ============================================================

CREATE TABLE session_experience_evidence (
    session_id UUID PRIMARY KEY REFERENCES interview_sessions(id) ON DELETE CASCADE,
    evidence_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE session_experience_evidence IS 'Serialized ExperienceEvidence state.';
COMMENT ON COLUMN session_experience_evidence.session_id IS 'Associated interview session.';
COMMENT ON COLUMN session_experience_evidence.evidence_json IS 'Serialized ExperienceEvidence model.';
COMMENT ON COLUMN session_experience_evidence.updated_at IS 'Evidence last update timestamp.';

CREATE INDEX idx_session_experience_evidence_json
ON session_experience_evidence
USING GIN (evidence_json);

-- ============================================================
-- TABLE: session_evaluations
-- ============================================================
--
-- Final interview artifact.
--
-- Stores:
--   - InterviewEvaluation
--   - Communication metrics
--   - Professional metrics
--   - LLM-generated feedback
--
-- This is the primary output consumed by candidates and
-- recruiters.
--
-- ============================================================

CREATE TABLE session_evaluations (
    session_id UUID PRIMARY KEY REFERENCES interview_sessions(id) ON DELETE CASCADE,
    overall_score DOUBLE PRECISION NOT NULL,
    communication_score DOUBLE PRECISION NOT NULL,
    professional_score DOUBLE PRECISION NOT NULL,
    assessment_confidence DOUBLE PRECISION NOT NULL,
    evaluation_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE session_evaluations IS 'Final interview evaluation artifact.';
COMMENT ON COLUMN session_evaluations.session_id IS 'Associated interview session.';
COMMENT ON COLUMN session_evaluations.overall_score IS 'Overall interview score.';
COMMENT ON COLUMN session_evaluations.communication_score IS 'Communication assessment score.';
COMMENT ON COLUMN session_evaluations.professional_score IS 'Professional competency score.';
COMMENT ON COLUMN session_evaluations.assessment_confidence IS 'Confidence level of the generated assessment.';
COMMENT ON COLUMN session_evaluations.evaluation_json IS 'Serialized InterviewEvaluation model.';
COMMENT ON COLUMN session_evaluations.created_at IS 'Evaluation creation timestamp.';

CREATE INDEX idx_session_evaluations_overall_score
ON session_evaluations(overall_score DESC);

CREATE INDEX idx_session_evaluations_confidence
ON session_evaluations(assessment_confidence DESC);

CREATE INDEX idx_session_evaluations_json
ON session_evaluations
USING GIN (evaluation_json);

-- ============================================================
-- VIEW: interview_results
-- ============================================================
--
-- Analytics-friendly projection used for:
--   - Dashboards
--   - Rankings
--   - Reporting
--   - Aggregate statistics
--
-- ============================================================

CREATE VIEW interview_results AS
SELECT
    s.id AS session_id,
    s.candidate_id,
    s.started_at,
    s.completed_at,
    e.overall_score,
    e.communication_score,
    e.professional_score,
    e.assessment_confidence
FROM interview_sessions s
JOIN session_evaluations e
    ON s.id = e.session_id;

COMMENT ON VIEW interview_results IS 'Analytics-friendly interview results projection.';