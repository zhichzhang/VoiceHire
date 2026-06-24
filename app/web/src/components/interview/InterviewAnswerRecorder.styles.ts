import type { CSSProperties } from "react";

export const recorderCardStyle: CSSProperties = {
  borderRadius: 24,
  border: "1px solid rgba(15, 23, 42, 0.08)",
  background: "rgba(255, 255, 255, 0.96)",
  boxShadow: "0 16px 40px rgba(15, 23, 42, 0.08)",
  padding: 22,
  display: "flex",
  flexDirection: "column",
  gap: 16,
  minWidth: 0,
};

export const recorderHeaderStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",

  gap: 12,

  borderBottom:
    "1px solid rgba(148,163,184,0.12)",

  paddingBottom: 12,
};
export const recorderTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: 20,
  fontWeight: 900,
  color: "#0f172a",
  lineHeight: 1.2,
};

export const recorderSubtitleStyle: CSSProperties = {
  marginTop: 4,
  fontSize: 13,
  color: "#64748b",
  lineHeight: 1.5,
};

export const recorderBadgeStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "6px 12px",
  borderRadius: 999,
  color: "#fff",
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: "0.02em",
  whiteSpace: "nowrap",
  background:
  "linear-gradient(90deg,#2563eb,#7c3aed)",
};

export const transcriptBoxStyle: CSSProperties = {
  minHeight: 280,
  padding: 18,
  borderRadius: 20,
  border: "1px solid rgba(148, 163, 184, 0.22)",
  background:
  "linear-gradient(180deg, rgba(248,250,255,0.98), rgba(255,255,255,0.98))",
  color: "#0f172a",
  fontSize: 17,
  lineHeight: 1.8,
  whiteSpace: "pre-wrap",
  overflowY: "auto",
  boxShadow:
  "inset 0 1px 2px rgba(15,23,42,0.03), 0 1px 0 rgba(255,255,255,0.9)",
};

export const waveformRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-end",
  gap: 4,
  minHeight: 72,
  paddingTop: 4,
};

export const waveformBarStyle: CSSProperties = {
  width: 7,
  borderRadius: 999,
  background:
  "linear-gradient(180deg,#2563eb 0%,#7c3aed 100%)",
  transition: "height 80ms linear, opacity 120ms ease",
};

export const footerRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 10,
  alignItems: "center",
  color: "#64748b",
  fontSize: 12,
  lineHeight: 1.5,
};

export const statusTextPillStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  padding: "6px 10px",
  borderRadius: 999,
  background: "#e2e8f0",
  color: "#334155",
  fontSize: 12,
  fontWeight: 700,
  lineHeight: 1,
};

export const recordingPillStyle: CSSProperties = {
  ...statusTextPillStyle,

  background:
    "linear-gradient(180deg,#dcfce7,#bbf7d0)",

  color: "#166534",
};

export const pausedPillStyle: CSSProperties = {
  ...statusTextPillStyle,

  background:
    "linear-gradient(180deg,#fee2e2,#fecaca)",

  color: "#991b1b",
};

export const compactHintStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 12,
  lineHeight: 1.5,
};
