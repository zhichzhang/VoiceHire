import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getInterviewReport } from "../../api/interviewApi";
import type {
  DimensionScore,
  InterviewEvaluation,
  InterviewReportResponse,
  InterviewTurn,
  PhaseEvaluation,
} from "../../types/api";
import {
  pageStyle,
  shellStyle,
  cardStyle,
  headingStyle,
  subheadingStyle,
  sectionTitleStyle,
  errorStyle,
  mutedTextStyle,
  primaryScoreStyle,
  metricGridStyle,
  metricCardStyle,
  metricLabelStyle,
  metricValueStyle,
  metricHintStyle,
  listStyle,
  listItemStyle,
  turnCardStyle,
  turnHeaderStyle,
  turnMetaStyle,
  turnQuestionStyle,
  turnAnswerStyle,
  chipStyle,
  chipRowStyle,
  buttonStyle,
  buttonRowStyle,
  emptyStateStyle,
  feedbackGridStyle,
  feedbackTextStyle,
  phaseCardStyle,
  dimensionCardStyle,
  dimensionNameStyle,
  dimensionScoreStyle,
  dimensionJustificationStyle,
  sectionHeaderCenteredStyle,
  sectionPanelStyle,
  sectionPanelTitleStyle,
  sectionPanelTextStyle,
  sectionBodyLabelStyle, centeredChipRowStyle, phaseResultHeaderStyle, recommendationCardStyle,
} from "./EvaluationPage.styles";

function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Math.round(value * 100)}%`;
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function renderList(items: string[] | undefined | null): ReactNode {
  if (!items || items.length === 0) {
    return <li style={listItemStyle}>—</li>;
  }

  return items.map((item, index) => (
    <li key={`${item}-${index}`} style={listItemStyle}>
      {item}
    </li>
  ));
}

function getTopScoreLabel(evaluation: InterviewEvaluation | null): string {
  if (!evaluation) return "—";
  return `${formatNumber(evaluation.overall_score)} / 100`;
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section style={cardStyle}>
      <div style={sectionHeaderCenteredStyle}>
        <h2 style={sectionTitleStyle}>{title}</h2>
        {subtitle ? <p style={subheadingStyle}>{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

function PanelCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div style={sectionPanelStyle}>
      <div style={sectionPanelTitleStyle}>{title}</div>
      {children}
    </div>
  );
}

function LabelValue({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div>
      <div style={sectionBodyLabelStyle}>{label}</div>
      <div style={sectionPanelTextStyle}>{value}</div>
    </div>
  );
}

function BulletList({ items }: { items?: string[] | null }) {
  return <ul style={listStyle}>{renderList(items)}</ul>;
}

export default function EvaluationPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState<InterviewReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    let cancelled = false;

    const loadReport = async () => {
      try {
        setLoading(true);
        setError(null);
        const payload = await getInterviewReport(sessionId);
        if (!cancelled) {
          setReport(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load report");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void loadReport();

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const session = report?.session ?? null;
  const evaluation = report?.evaluation ?? null;
  const turns = report?.turns ?? [];
  const communicationMetrics = evaluation?.communication_metrics ?? null;
  const phaseResults = useMemo(() => evaluation?.phase_results ?? [], [evaluation]);
  const recommendationCount = evaluation?.llm_feedback?.recommendations?.length ?? 0;

  if (!sessionId) {
    return (
      <div style={pageStyle}>
        <div style={shellStyle}>
          <header style={cardStyle}>
            <div style={sectionHeaderCenteredStyle}>
              <h1 style={headingStyle}>Evaluation</h1>
              <p style={subheadingStyle}>Missing session id.</p>
            </div>
            <div style={buttonRowStyle}>
              <button type="button" style={buttonStyle} onClick={() => navigate("/")}>
                Back to landing
              </button>
            </div>
          </header>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={pageStyle}>
        <div style={shellStyle}>
          <header style={cardStyle}>
            <div style={sectionHeaderCenteredStyle}>
              <h1 style={headingStyle}>Evaluation</h1>
              <p style={subheadingStyle}>Loading report…</p>
            </div>
          </header>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={pageStyle}>
        <div style={shellStyle}>
          <header style={cardStyle}>
            <div style={sectionHeaderCenteredStyle}>
              <h1 style={headingStyle}>Evaluation</h1>
              <p style={subheadingStyle}>Could not load the report.</p>
            </div>
            <p style={errorStyle}>{error}</p>
            <div style={buttonRowStyle}>
              <button type="button" style={buttonStyle} onClick={() => navigate("/")}>
                Back to landing
              </button>
            </div>
          </header>
        </div>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <div style={shellStyle}>
        <header style={cardStyle}>
          <div style={sectionHeaderCenteredStyle}>
            <div style={centeredChipRowStyle}>
              <span style={chipStyle}>Session</span>
              <span style={chipStyle}>{session?.session_id ?? sessionId}</span>
              <span style={chipStyle}>Status: {session?.status ?? "—"}</span>
              <span style={chipStyle}>Phase: {session?.current_phase ?? "—"}</span>
            </div>

            <h1 style={headingStyle}>Evaluation</h1>
            <p style={subheadingStyle}>
              Final interview report generated from the full transcript, turn-level scoring,
              and LLM feedback.
            </p>
          </div>

          <div style={metricGridStyle}>
            <div style={metricCardStyle}>
              <div style={metricLabelStyle}>Overall score</div>
              <div style={primaryScoreStyle}>{getTopScoreLabel(evaluation)}</div>
              <div style={metricHintStyle}>Final weighted score</div>
            </div>

            <div style={metricCardStyle}>
              <div style={metricLabelStyle}>Communication</div>
              <div style={metricValueStyle}>
                {formatNumber(evaluation?.communication_score)} / 100
              </div>
              <div style={metricHintStyle}>Relevance · clarity · fluency</div>
            </div>

            <div style={metricCardStyle}>
              <div style={metricLabelStyle}>Professional</div>
              <div style={metricValueStyle}>
                {formatNumber(evaluation?.professional_score)} / 100
              </div>
              <div style={metricHintStyle}>Phase-level competency aggregation</div>
            </div>

            <div style={metricCardStyle}>
              <div style={metricLabelStyle}>Confidence</div>
              <div style={metricValueStyle}>
                {formatPercent(evaluation?.assessment_confidence)}
              </div>
              <div style={metricHintStyle}>LLM confidence</div>
            </div>
          </div>

          <div style={buttonRowStyle}>
            <button type="button" style={buttonStyle} onClick={() => navigate("/")}>
              Back to landing
            </button>
          </div>
        </header>

        <SectionCard
          title="Summary"
          subtitle="High-level feedback and the candidate context used by the evaluator."
        >
          <div style={feedbackGridStyle}>
            <PanelCard title="LLM Summary">
              <p style={feedbackTextStyle}>{evaluation?.llm_feedback?.summary ?? "—"}</p>
            </PanelCard>

            <PanelCard title="Candidate context">
              <div style={{ display: "grid", gap: 14 }}>
                <LabelValue
                  label="Most recent role"
                  value={session?.candidate_profile?.most_recent_role ?? "—"}
                />

                <div style={{ display: "grid", gap: 10 }}>
                  <div style={sectionBodyLabelStyle}>Experience evidence</div>
                  <div style={{ display: "grid", gap: 8 }}>
                    <LabelValue
                      label="Type"
                      value={session?.experience_evidence?.experience_type ?? "—"}
                    />
                    <LabelValue
                      label="Name"
                      value={session?.experience_evidence?.experience_name ?? "—"}
                    />
                    <LabelValue label="What" value={session?.experience_evidence?.what ?? "—"} />
                    <LabelValue label="Why" value={session?.experience_evidence?.why ?? "—"} />
                    <LabelValue label="How" value={session?.experience_evidence?.how ?? "—"} />
                    <LabelValue
                      label="Challenge"
                      value={session?.experience_evidence?.challenge ?? "—"}
                    />
                    <LabelValue
                      label="Outcome"
                      value={session?.experience_evidence?.outcome ?? "—"}
                    />
                  </div>
                </div>
              </div>
            </PanelCard>
          </div>
        </SectionCard>

        <SectionCard
          title="Strengths / Weaknesses / Recommendations"
          subtitle="Three vertically stacked sections for easier scanning."
        >
          <div style={{ display: "grid", gap: 16 }}>
            <PanelCard title="Strengths">
              <BulletList items={evaluation?.llm_feedback?.strengths} />
            </PanelCard>

            <PanelCard title="Weaknesses">
              <BulletList items={evaluation?.llm_feedback?.weaknesses} />
            </PanelCard>

            <PanelCard title={`Recommendations (${recommendationCount})`}>
              {evaluation?.llm_feedback?.recommendations?.length ? (
                <div style={{ display: "grid", gap: 12 }}>
                  {evaluation.llm_feedback.recommendations.map((item, index) => (
                    <div key={`${item.category}-${index}`} style={recommendationCardStyle}>
                      <div style={centeredChipRowStyle}>
                        <span style={chipStyle}>{item.category}</span>
                        <span style={chipStyle}>{item.priority}</span>
                      </div>
                      <p style={{ ...feedbackTextStyle, textAlign: "left" }}>
                        {item.recommendation}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={mutedTextStyle}>—</p>
              )}
            </PanelCard>
          </div>
        </SectionCard>

        <SectionCard
          title="Phase Results"
          subtitle="Scores and observations for each interview phase."
        >
          {phaseResults.length ? (
            <div style={{ display: "grid", gap: 16 }}>
              {phaseResults.map((phase: PhaseEvaluation) => (
                <article key={phase.phase_name} style={phaseCardStyle}>
                  <div style={phaseResultHeaderStyle}>
                    <span style={chipStyle}>{phase.phase_name}</span>
                    <span style={chipStyle}>
                      Score: {phase.overall_score.toFixed(1)} / 100
                    </span>
                  </div>

                  <div style={{ display: "grid", gap: 12 }}>
                    {phase.dimensions.map((dimension: DimensionScore) => (
                      <div key={dimension.name} style={dimensionCardStyle}>
                            <div style={dimensionNameStyle}>{dimension.name}</div>
                            <div style={dimensionScoreStyle}>
                              {formatNumber(dimension.score)} / 100
                            </div>
                            <div style={dimensionJustificationStyle}>
                              {dimension.justification}
                            </div>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: "grid", gap: 16 }}>
                    <PanelCard title="Strengths">
                      <BulletList items={phase.strengths} />
                    </PanelCard>

                    <PanelCard title="Improvements">
                      <BulletList items={phase.improvements} />
                    </PanelCard>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p style={emptyStateStyle}>No phase results yet.</p>
          )}
        </SectionCard>

        <SectionCard
          title="Communication Metrics"
          subtitle="Relevance, clarity, and fluency scores derived from the turn assessments."
        >
          {communicationMetrics ? (
            <div style={metricGridStyle}>
              <div style={metricCardStyle}>
                <div style={metricLabelStyle}>Relevance</div>
                <div style={metricValueStyle}>
                  {formatNumber(communicationMetrics.relevance)}
                </div>
                <div style={metricHintStyle}>Answer alignment to the question</div>
              </div>

              <div style={metricCardStyle}>
                <div style={metricLabelStyle}>Clarity</div>
                <div style={metricValueStyle}>
                  {formatNumber(communicationMetrics.clarity)}
                </div>
                <div style={metricHintStyle}>Structure and readability</div>
              </div>

              <div style={metricCardStyle}>
                <div style={metricLabelStyle}>Fluency</div>
                <div style={metricValueStyle}>
                  {formatNumber(communicationMetrics.fluency)}
                </div>
                <div style={metricHintStyle}>Naturalness and flow</div>
              </div>
            </div>
          ) : (
            <p style={emptyStateStyle}>No communication metrics available.</p>
          )}
        </SectionCard>

        <SectionCard
          title="Turns"
          subtitle="Question, answer, and turn-level scoring rendered in the same card style."
        >
          {turns.length ? (
            <div style={{ display: "grid", gap: 16 }}>
              {turns.map((turn: InterviewTurn) => (
                <article
                  key={`${turn.turn_number ?? turn.question}-${turn.phase}`}
                  style={turnCardStyle}
                >
                  <div style={turnHeaderStyle}>
                    <div style={chipRowStyle}>
                      <span style={chipStyle}>Turn {turn.turn_number ?? "—"}</span>
                      <span style={chipStyle}>{turn.phase}</span>
                      <span style={chipStyle}>{turn.assessment_status}</span>
                    </div>
                    <div style={turnMetaStyle}>
                      Assessed: {formatDateTime(turn.assessed_at)}
                    </div>
                  </div>

                  <div>
                    <div style={sectionBodyLabelStyle}>Question</div>
                    <div style={turnQuestionStyle}>{turn.question}</div>
                  </div>

                  <div>
                    <div style={sectionBodyLabelStyle}>Answer</div>
                    <div style={turnAnswerStyle}>{turn.answer}</div>
                  </div>

                  <div style={metricGridStyle}>
                    <div style={metricCardStyle}>
                      <div style={metricLabelStyle}>Relevance</div>
                      <div style={metricValueStyle}>
                        {formatNumber(turn.assessment?.relevance)}
                      </div>
                    </div>
                    <div style={metricCardStyle}>
                      <div style={metricLabelStyle}>Clarity</div>
                      <div style={metricValueStyle}>
                        {formatNumber(turn.assessment?.clarity)}
                      </div>
                    </div>
                    <div style={metricCardStyle}>
                      <div style={metricLabelStyle}>Fluency</div>
                      <div style={metricValueStyle}>
                        {formatNumber(turn.assessment?.fluency)}
                      </div>
                    </div>
                  </div>

                  {turn.assessment_error ? (
                    <p style={errorStyle}>{turn.assessment_error}</p>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <p style={emptyStateStyle}>No turns recorded yet.</p>
          )}
        </SectionCard>

        <footer style={cardStyle}>
          <div style={centeredChipRowStyle}>
            <span style={chipStyle}>Started: {formatDateTime(session?.started_at)}</span>
            <span style={chipStyle}>Completed: {formatDateTime(session?.completed_at)}</span>
            <span style={chipStyle}>Expires: {formatDateTime(session?.expires_at)}</span>
          </div>
          <p style={mutedTextStyle}>
            Candidate profile, resume context, and transcript records are rendered directly
            from the report payload.
          </p>
        </footer>
      </div>
    </div>
  );
}