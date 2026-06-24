import type { CSSProperties } from "react";

export const pageStyle: CSSProperties = {
  minHeight: "100vh",
  padding: "32px 20px 44px",

  display: "flex",
  justifyContent: "center",
  alignItems: "flex-start",

  background:
    "radial-gradient(circle at 14% 12%, rgba(255,255,255,0.98) 0%, rgba(250,252,255,1) 34%, rgba(240,244,255,1) 100%)",
};

export const layoutStyle: CSSProperties = {
  width: "min(1120px, 100%)",
  display: "flex",
  flexDirection: "column",
  gap: 20,
  alignItems: "stretch",
};

export const cardStyle: CSSProperties = {
  borderRadius: 30,

  border: "1px solid rgba(148,163,184,0.18)",

  background:
    "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(253,253,255,0.98) 100%)",

  boxShadow: "0 18px 46px rgba(15,23,42,0.08)",

  padding: 28,

  display: "flex",
  flexDirection: "column",
  gap: 18,

  minWidth: 0,
};

export const loadingCardStyle: CSSProperties = {
  ...cardStyle,
  width: "min(760px, 100%)",
  minHeight: 380,
  justifyContent: "center",
  alignItems: "center",
  textAlign: "center",
  margin: "0 auto",
};

export const loadingSpinnerStyle: CSSProperties = {
  width: 42,
  height: 42,
  borderRadius: "50%",

  border: "4px solid rgba(148, 163, 184, 0.25)",

  borderTopColor: "#2563eb",
  borderRightColor: "#7c3aed",

  animation: "spin 1s linear infinite",
};

export const sectionTitleStyle: CSSProperties = {
  margin: 0,

  fontSize: 34,

  lineHeight: 1.08,

  letterSpacing: "-0.04em",

  fontWeight: 900,

  color: "transparent",

  backgroundImage:
    "linear-gradient(90deg,#2563eb 0%,#4f46e5 35%,#7c3aed 72%,#d946ef 100%)",

  backgroundClip: "text",
  WebkitBackgroundClip: "text",

  WebkitTextFillColor: "transparent",
};

export const questionStyle: CSSProperties = {
  minHeight: 144,

  padding: 22,

  borderRadius: 20,

  border: "1px solid rgba(148, 163, 184, 0.22)",

  background:
    "linear-gradient(180deg, rgba(248,250,255,0.98), rgba(255,255,255,0.98))",

  boxShadow: "0 8px 20px rgba(15,23,42,0.04)",

  color: "#0f172a",

  fontSize: 22,

  lineHeight: 1.7,

  whiteSpace: "pre-wrap",

  overflowY: "auto",
};

export const metaRowStyle: CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: 10,
  alignItems: "center",
  color: "#334155",
  fontSize: 13,
};

export const chipStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "7px 12px",
  borderRadius: 999,
  background: "#e2e8f0",
  color: "#334155",
  fontSize: 12,
  fontWeight: 700,
  lineHeight: 1,
};

export const primaryChipStyle: CSSProperties = {
  ...chipStyle,
  background:
    "linear-gradient(90deg,#2563eb 0%,#7c3aed 100%)",
  color: "#ffffff",
};

export const buttonRowStyle: CSSProperties = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap",
  alignItems: "center",
};

export const buttonStyle: CSSProperties = {
  appearance: "none",
  border: "none",
  borderRadius: 16,
  padding: "13px 18px",
  background:
  "linear-gradient(90deg,#2563eb 0%,#4f46e5 35%,#7c3aed 70%,#d946ef 100%)",
  color: "#fff",
  fontSize: 15,
  fontWeight: 800,
  cursor: "pointer",
  userSelect: "none",
  WebkitTapHighlightColor: "transparent",
  touchAction: "manipulation",
  transition:
    "transform 0.16s ease, opacity 0.15s ease, box-shadow 0.16s ease, filter 0.16s ease",
  willChange: "transform",
  boxShadow: "0 10px 24px rgba(17, 24, 39, 0.12)",
};

export const secondaryButtonStyle: CSSProperties = {
  ...buttonStyle,
  background:
  "linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,255,0.98))",
  color: "#111827",
  border: "1px solid rgba(148, 163, 184, 0.35)",
};

export const dangerButtonStyle: CSSProperties = {
  ...buttonStyle,
  background: "#b91c1c",
};

export const disabledButtonStyle: CSSProperties = {
  opacity: 0.52,
  cursor: "not-allowed",
  boxShadow: "none",
};

export const errorStyle: CSSProperties = {
  margin: 0,
  color: "#b91c1c",
  fontSize: 14,
  lineHeight: 1.6,
  background: "#fef2f2",
  border: "1px solid rgba(185, 28, 28, 0.18)",
  borderRadius: 14,
  padding: "12px 14px",
};

export const helperTextStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 13,
  lineHeight: 1.55,
};

export const statusTextStyle: CSSProperties = {
  margin: 0,
  color: "#334155",
  fontSize: 13,
  lineHeight: 1.55,
};

export const countdownHeroStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",

  alignItems: "center",

  justifyContent: "center",

  gap: 10,

  padding: "28px 22px",

  borderRadius: 24,

  background:
    "linear-gradient(180deg, rgba(239,244,255,0.98), rgba(248,250,255,0.98))",

  border: "1px solid rgba(99,102,241,0.14)",

  boxShadow: "0 8px 20px rgba(99,102,241,0.08)",
};

export const countdownLabelStyle: CSSProperties = {
  fontSize: 14,
  fontWeight: 800,
  color: "#1e40af",
  textTransform: "uppercase",
  letterSpacing: "0.08em",
};

export const countdownValueStyle: CSSProperties = {
  fontSize: 72,

  fontWeight: 900,

  lineHeight: 1,

  letterSpacing: "-0.04em",

  color: "transparent",

  backgroundImage:
    "linear-gradient(90deg,#2563eb,#7c3aed,#ec4899)",

  backgroundClip: "text",
  WebkitBackgroundClip: "text",

  WebkitTextFillColor: "transparent",
};

export const countdownHintStyle: CSSProperties = {
  fontSize: 13,
  color: "#475569",
  textAlign: "center",
  lineHeight: 1.5,
};

export const readingProgressStyle: CSSProperties = {
  height: 8,
  width: "100%",
  borderRadius: 999,
  background: "#dbeafe",
  overflow: "hidden",
};

export const readingProgressBarStyle: CSSProperties = {
  height: "100%",
  borderRadius: 999,
  background:
  "linear-gradient(90deg,#2563eb 0%,#7c3aed 60%,#ec4899 100%)",
  transition: "width 0.2s linear",
};

export const footerNoticeStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 12,
  lineHeight: 1.5,
};

export const statusPillStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  flexWrap: "wrap",
  gap: 8,
  padding: "8px 12px",
  borderRadius: 999,
  fontSize: 12,
  fontWeight: 700,
  lineHeight: 1,
  background:
  "linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,255,0.98))",
  color: "#334155",
  border: "1px solid rgba(148, 163, 184, 0.22)",
  boxShadow: "0 4px 12px rgba(15,23,42,0.04)",
};
