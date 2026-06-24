import type { CSSProperties } from "react";

export const pageStyle: CSSProperties = {
  minHeight: "100vh",

  padding: 24,

  background:
    "radial-gradient(circle at 14% 12%, rgba(255,255,255,0.98) 0%, rgba(250,252,255,1) 34%, rgba(240,244,255,1) 100%)",

  boxSizing: "border-box",
};

export const shellStyle: CSSProperties = {
  width: "min(1200px, 100%)",
  margin: "0 auto",
  display: "grid",
  gap: 20,
};

export const cardStyle: CSSProperties = {
  borderRadius: 30,
  border:
  "1px solid rgba(148,163,184,0.18)",
  background:
  "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(253,253,255,0.98) 100%)",
  boxShadow:
  "0 18px 46px rgba(15,23,42,0.08)",
  padding: 24,
  display: "grid",
  gap: 18,
};

export const headingStyle: CSSProperties = {
  margin: 0,

  fontSize: "clamp(30px,4vw,46px)",

  fontWeight: 900,

  lineHeight: 1.05,

  letterSpacing: "-0.04em",

  color: "transparent",

  backgroundImage:
    "linear-gradient(90deg,#2563eb 0%,#4f46e5 35%,#7c3aed 72%,#d946ef 100%)",

  backgroundClip: "text",
  WebkitBackgroundClip: "text",

  WebkitTextFillColor: "transparent",

  textAlign: "center",
};

export const subheadingStyle: CSSProperties = {
  margin: 0,
  color: "#475569",
  lineHeight: 1.7,
  fontSize: 15,
  textAlign: "center",
  maxWidth: 780,
};

export const sectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: "clamp(20px, 2.2vw, 28px)",
  lineHeight: 1.15,
  letterSpacing: "-0.03em",
  color: "#0f172a",
  fontWeight: 800,
  textAlign: "center",
};

export const sectionHeaderCenteredStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  justifyItems: "center",
  textAlign: "center",
};

export const sectionHeaderStyle: CSSProperties = {
  display: "grid",
  gap: 10,
};

export const sectionPanelStyle: CSSProperties = {
  background:
  "linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(248,250,255,0.96) 100%)",

  boxShadow:
    "0 10px 26px rgba(15,23,42,0.05)",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 18,
  padding: 18,
  display: "grid",
  gap: 12,
};

export const sectionPanelTitleStyle: CSSProperties = {
  margin: 0,
  color: "#0f172a",
  fontSize: 14,
  fontWeight: 800,
  lineHeight: 1.3,
  letterSpacing: "-0.01em",
  textAlign: "center",
};

export const sectionPanelTextStyle: CSSProperties = {
  margin: 0,
  color: "#334155",
  lineHeight: 1.7,
  fontSize: 14,
  whiteSpace: "pre-wrap",
};

export const sectionBodyLabelStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 12,
  fontWeight: 800,
  textTransform: "uppercase",
  letterSpacing: "0.08em",
};

export const errorStyle: CSSProperties = {
  margin: 0,
  color: "#b91c1c",
  background: "#fef2f2",
  border: "1px solid rgba(185, 28, 28, 0.18)",
  borderRadius: 14,
  padding: "12px 14px",
  lineHeight: 1.6,
};

export const helperTextStyle: CSSProperties = {
  margin: 0,
  color: "#334155",
  lineHeight: 1.65,
  fontSize: 14,
};

export const mutedTextStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  lineHeight: 1.65,
  fontSize: 14,
  textAlign: "center"
};

export const primaryScoreStyle: CSSProperties = {
  fontSize: 34,

  fontWeight: 900,

  lineHeight: 1,

  color: "transparent",

  backgroundImage:
    "linear-gradient(90deg,#2563eb,#7c3aed,#ec4899)",

  backgroundClip: "text",
  WebkitBackgroundClip: "text",

  WebkitTextFillColor: "transparent",
};
export const metricGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: 14,
  marginTop: 18,
};

export const metricCardStyle: CSSProperties = {
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(248,250,255,0.96) 100%)",
  border: "1px solid rgba(148,163,184,0.16)",
  boxShadow: "0 10px 26px rgba(15,23,42,0.05)",
  borderRadius: 16,
  padding: 16,
  display: "grid",
  gap: 8,
  justifyItems: "center",
  textAlign: "center",
};

export const metricLabelStyle: CSSProperties = {
  color: "#64748b",
  fontSize: 13,
  marginBottom: 0,
  fontWeight: 700,
  textAlign: "center",
};

export const metricValueStyle: CSSProperties = {
  color: "#0f172a",
  fontSize: 28,
  fontWeight: 800,
  lineHeight: 1.1,
  textAlign: "center",
};

export const metricHintStyle: CSSProperties = {
  marginTop: 0,
  color: "#64748b",
  fontSize: 12,
  lineHeight: 1.5,
  textAlign: "center",
};

export const listStyle: CSSProperties = {
  margin: 0,
  paddingLeft: 18,
  display: "grid",
  gap: 8,
};

export const listItemStyle: CSSProperties = {
  color: "#0f172a",
  lineHeight: 1.6,
  fontSize: 14,
};

export const turnCardStyle: CSSProperties = {
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 18,
  padding: 18,
  display: "grid",
  gap: 14,
};

export const turnHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 12,
  flexWrap: "wrap",
};

export const turnMetaStyle: CSSProperties = {
  color: "#64748b",
  fontSize: 12,
};

export const turnQuestionStyle: CSSProperties = {
  color: "#0f172a",
  lineHeight: 1.7,
  fontSize: 15,
  whiteSpace: "pre-wrap",
};

export const turnAnswerStyle: CSSProperties = {
  color: "#334155",
  lineHeight: 1.7,
  fontSize: 15,
  whiteSpace: "pre-wrap",
};

export const chipRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
};

export const chipStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 10px",
  borderRadius: 999,
  background:
  "linear-gradient(180deg, rgba(239,244,255,0.98), rgba(226,233,255,0.98))",

  border:
    "1px solid rgba(99,102,241,0.14)",

  boxShadow:
    "0 8px 18px rgba(99,102,241,0.08)",
  color: "#3730a3",
  fontSize: 12,
  fontWeight: 700,
  lineHeight: 1,
};

export const buttonStyle: CSSProperties = {
  appearance: "none",
  border: "none",
  borderRadius: 14,
  padding: "12px 18px",
  background:
  "linear-gradient(90deg,#2563eb 0%,#4f46e5 35%,#7c3aed 70%,#d946ef 100%)",

  boxShadow:
    "0 14px 30px rgba(76,81,191,0.18)",
  color: "#ffffff",
  fontSize: 15,
  fontWeight: 700,
  cursor: "pointer",
  userSelect: "none",
  WebkitTapHighlightColor: "transparent",
  touchAction: "manipulation",
  transition:
    "transform 0.16s ease, opacity 0.15s ease, box-shadow 0.16s ease, filter 0.16s ease",
  willChange: "transform",
};

export const buttonRowStyle: CSSProperties = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap",
  marginTop: 18,
  justifyContent: "center",
};

export const emptyStateStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 14,
  lineHeight: 1.6,
};

export const feedbackGridStyle: CSSProperties = {
  display: "grid",
  gap: 16,
};

export const feedbackPanelStyle: CSSProperties = {
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 18,
  padding: 16,
  display: "grid",
  gap: 12,
};

export const feedbackTextStyle: CSSProperties = {
  margin: 0,
  color: "#0f172a",
  lineHeight: 1.7,
  fontSize: 14,
  whiteSpace: "pre-wrap",
};

export const phaseCardStyle: CSSProperties = {
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 18,
  padding: 18,
  display: "grid",
  gap: 16,
};

export const dimensionCardStyle: CSSProperties = {
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 14,
  padding: 14,
  display: "grid",
  gap: 8,
  justifyItems: "center",
  textAlign: "center",
};

export const dimensionNameStyle: CSSProperties = {
  textAlign: "center",
  fontWeight: 700,
  marginBottom: 8,
};

export const dimensionScoreStyle: CSSProperties = {
  textAlign: "center",
  fontSize: 18,
  fontWeight: 800,
  marginBottom: 16,
};

export const dimensionJustificationStyle: CSSProperties = {
  color: "#475569",
  fontSize: 14,
  lineHeight: 1.6,

  width: "100%",
  textAlign: "left",
};

export const centeredChipRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 8,
  justifyContent: "center",
};

export const recommendationCardStyle: CSSProperties = {
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 14,
  padding: 14,
  display: "grid",
  gap: 10,
  justifyItems: "center",
  textAlign: "center",
};

export const phaseResultHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "center",
  gap: 12,
  flexWrap: "wrap",
  marginBottom: 16,
};