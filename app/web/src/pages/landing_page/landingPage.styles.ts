// app/web/src/pages/landing_page/landingPage.styles.ts

import type { CSSProperties } from "react";

export const pageStyle: CSSProperties = {
  minHeight: "100vh",
  padding: "20px",
  display: "flex",
  justifyContent: "center",
  alignItems: "stretch",
  background:
    "radial-gradient(circle at 14% 12%, rgba(255,255,255,0.98) 0%, rgba(250,252,255,1) 34%, rgba(240,244,255,1) 100%)",
  boxSizing: "border-box",
};

export const shellStyle: CSSProperties = {
  width: "min(1400px, 100%)",
  display: "grid",
  gridTemplateColumns: "minmax(0, 1.04fr) minmax(0, 1fr)",
  gap: 24,
  alignItems: "stretch",
};

export const heroCardStyle: CSSProperties = {
  padding: 32,
  borderRadius: 30,
  border: "1px solid rgba(148, 163, 184, 0.18)",
  background:
    "radial-gradient(circle at 18% 8%, rgba(99, 102, 241, 0.06) 0, transparent 26%), radial-gradient(circle at 82% 16%, rgba(236, 72, 153, 0.05) 0, transparent 24%), linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,249,255,0.98) 100%)",
  boxShadow: "0 18px 46px rgba(15, 23, 42, 0.08)",
  display: "grid",
  gridTemplateRows: "auto auto auto auto",
  gap: 16,
  minHeight: "100%",
  height: "100%",
  alignSelf: "stretch",
  overflow: "hidden",
};

export const heroTopStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "flex-start",
};

export const heroContentStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  justifyItems: "center",
  textAlign: "center",
  alignSelf: "start",
  width: "100%",
  paddingTop: 10,
  paddingBottom: 2,
};

export const formCardStyle: CSSProperties = {
  padding: 32,
  borderRadius: 30,
  border: "1px solid rgba(148, 163, 184, 0.18)",
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(253,253,255,0.98) 100%)",
  boxShadow: "0 18px 46px rgba(15, 23, 42, 0.08)",
  display: "grid",
  gap: 18,
  minHeight: "100%",
  height: "100%",
  alignSelf: "stretch",
  alignContent: "start",
};

export const badgeStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  padding: "8px 14px",
  borderRadius: 999,
  fontSize: 13,
  fontWeight: 800,
  letterSpacing: "0.01em",
  color: "#1d4ed8",
  background:
    "linear-gradient(180deg, rgba(239,244,255,0.98), rgba(226,233,255,0.98))",
  border: "1px solid rgba(99, 102, 241, 0.14)",
  boxShadow: "0 8px 18px rgba(99, 102, 241, 0.08)",
};

export const titleStyle: CSSProperties = {
  margin: 0,
  maxWidth: "min(14rem, 100%)",
  fontSize: "clamp(3rem, 6vw, 5.6rem)",
  lineHeight: 0.94,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  fontWeight: 900,
  fontFamily:
    'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace',
  color: "transparent",
  backgroundImage:
    "linear-gradient(90deg, #1d4ed8 0%, #4f46e5 28%, #7c3aed 58%, #db2777 100%)",
  backgroundClip: "text",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  textShadow:
    "0 0 6px rgba(99,102,241,0.12), 0 0 14px rgba(236,72,153,0.08)",
};

export const subtitleStyle: CSSProperties = {
  margin: 0,
  maxWidth: "min(34rem, 100%)",
  fontSize: "clamp(1rem, 1.2vw, 1.125rem)",
  lineHeight: 1.8,
  color: "#546075",
  textAlign: "center",
};

export const heroListStyle: CSSProperties = {
  margin: 0,
  padding: 0,
  listStyle: "none",
  display: "grid",
  gap: 14,
  alignSelf: "start",
  marginTop: 6,
  width: "100%",
};

export const heroListItemStyle: CSSProperties = {
  minHeight: 84,
  padding: "18px 20px",
  borderRadius: 18,
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.92) 0%, rgba(248,250,255,0.96) 100%)",
  border: "1px solid rgba(148, 163, 184, 0.16)",
  borderLeft: "3px solid rgba(59, 130, 246, 0.72)",
  boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
  color: "#0f172a",
  fontSize: "clamp(0.95rem, 1.1vw, 1.1rem)",
  lineHeight: 1.55,
  display: "flex",
  alignItems: "center",
  fontWeight: 600,
};

export const fieldHintStyle: CSSProperties = {
  margin: "6px 0 0",
  color: "#64748b",
  fontSize: "clamp(0.9rem, 1vw, 1rem)",
  lineHeight: 1.7,
  textAlign: "center",
  alignSelf: "start",
  maxWidth: "min(34rem, 100%)",
  justifySelf: "center",
};

export const formTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: 24,
  lineHeight: 1.15,
  fontWeight: 900,
  letterSpacing: "-0.03em",
  color: "transparent",
  backgroundImage:
    "linear-gradient(90deg, #2563eb 0%, #4f46e5 35%, #7c3aed 72%, #d946ef 100%)",
  backgroundClip: "text",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
};

export const sectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: 20,
  lineHeight: 1.2,
  color: "#0f172a",
  fontWeight: 900,
  letterSpacing: "-0.03em",
};

export const inputRowStyle: CSSProperties = {
  display: "grid",
  gap: 16,
};

export const sectionStackStyle: CSSProperties = {
  display: "grid",
  gap: 16,
};

export const labelStyle: CSSProperties = {
  display: "grid",
  gap: 8,
  fontSize: 14,
  fontWeight: 700,
  color: "#111827",
};

export const inputStyle: CSSProperties = {
  width: "100%",
  padding: "15px 16px",
  borderRadius: 16,
  border: "1px solid rgba(148, 163, 184, 0.28)",
  fontSize: 15,
  outline: "none",
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,255,0.98))",
  color: "#111827",
  boxSizing: "border-box",
  boxShadow:
    "inset 0 1px 2px rgba(15, 23, 42, 0.03), 0 1px 0 rgba(255,255,255,0.9)",
};

export const sessionInputStyle: CSSProperties = {
  ...inputStyle,
  fontFamily:
    "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  letterSpacing: "0.01em",
};

export const textareaStyle: CSSProperties = {
  ...inputStyle,
  minHeight: 220,
  resize: "vertical",
  lineHeight: 1.6,
  fontFamily: "inherit",
};

export const buttonStyle: CSSProperties = {
  width: "100%",
  padding: "14px 18px",
  borderRadius: 16,
  border: "none",
  background:
    "linear-gradient(90deg, #2563eb 0%, #4f46e5 35%, #7c3aed 70%, #d946ef 100%)",
  color: "white",
  fontWeight: 800,
  fontSize: 16,
  cursor: "pointer",
  userSelect: "none",
  WebkitTapHighlightColor: "transparent",
  touchAction: "manipulation",
  transition:
    "transform 0.16s ease, opacity 0.15s ease, box-shadow 0.16s ease, filter 0.16s ease",
  willChange: "transform",
  boxShadow: "0 14px 30px rgba(76, 81, 191, 0.18)",
};

export const secondaryButtonStyle: CSSProperties = {
  ...buttonStyle,
  background: "linear-gradient(180deg, rgba(255,255,255,0.98), #ffffff)",
  color: "#0ea5b7",
  border: "1px solid rgba(45, 212, 191, 0.42)",
  boxShadow: "0 10px 22px rgba(14, 165, 233, 0.07)",
};

export const disabledButtonStyle: CSSProperties = {
  opacity: 0.45,
  cursor: "not-allowed",
  transform: "none",
  boxShadow: "none",
  filter: "grayscale(0.04)",
};

export const dividerStyle: CSSProperties = {
  width: "100%",
  height: 1,
  background:
    "linear-gradient(90deg, transparent 0%, rgba(148, 163, 184, 0.28) 18%, rgba(148, 163, 184, 0.28) 82%, transparent 100%)",
};

export const noteStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 14,
  lineHeight: 1.7,
};

export const errorStyle: CSSProperties = {
  color: "#dc2626",
  fontSize: 14,
  margin: 0,
  lineHeight: 1.6,
};

export const modalOverlayStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(15, 23, 42, 0.42)",
  backdropFilter: "blur(6px)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 20,
  zIndex: 50,
};

export const modalCardStyle: CSSProperties = {
  width: "min(540px, 100%)",
  borderRadius: 22,
  background: "rgba(255,255,255,0.98)",
  boxShadow: "0 30px 90px rgba(15, 23, 42, 0.22)",
  border: "1px solid rgba(148, 163, 184, 0.2)",
  padding: 24,
  display: "grid",
  gap: 14,
};

export const modalTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: 22,
  lineHeight: 1.15,
  fontWeight: 900,
  color: "#0f172a",
  letterSpacing: "-0.03em",
};

export const modalMessageStyle: CSSProperties = {
  margin: 0,
  color: "#334155",
  lineHeight: 1.75,
  fontSize: 15,
};

export const modalActionsStyle: CSSProperties = {
  display: "flex",
  justifyContent: "flex-end",
  gap: 12,
};

export const modalOkButtonStyle: CSSProperties = {
  ...buttonStyle,
  width: "auto",
  minWidth: 112,
  padding: "12px 18px",
};

export const formSeparatorStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr auto 1fr",
  alignItems: "center",
  gap: 12,
  marginTop: 8,
  marginBottom: 2,
};

export const formSeparatorLineStyle: CSSProperties = {
  height: 1,
  background:
    "linear-gradient(90deg, rgba(226,232,240,0) 0%, rgba(226,232,240,1) 12%, rgba(226,232,240,1) 88%, rgba(226,232,240,0) 100%)",
};

export const formSeparatorPillStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minWidth: 42,
  padding: "4px 12px",
  borderRadius: 999,
  border: "1px solid rgba(226,232,240,1)",
  background: "#f8fafc",
  color: "#64748b",
  fontSize: 12,
  fontWeight: 800,
  boxShadow: "0 2px 4px rgba(15,23,42,0.04)",
};

export const resumeHeaderStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
};

export const resumeIconStyle: CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: 999,
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#0ea5b7",
  background: "rgba(14, 165, 233, 0.10)",
  border: "1px solid rgba(14, 165, 233, 0.20)",
  boxShadow: "0 8px 20px rgba(14, 165, 233, 0.08)",
  fontSize: 14,
  fontWeight: 900,
};

export const heroMarqueeStyle: CSSProperties = {
  width: "100%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",

  marginTop: "8px",
  marginBottom: "16px",

  overflow: "hidden",
};

export const heroMarqueeTrackStyle: CSSProperties = {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",

  width: "100%",
};

export const heroMarqueeWordStyle: CSSProperties = {
  fontSize: "clamp(2.8rem, 8vw, 6rem)",
  fontWeight: 900,
  lineHeight: 1,
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  textAlign: "center",
  whiteSpace: "nowrap",
  backgroundImage:
    "linear-gradient(90deg, #2563eb 0%, #4f46e5 20%, #7c3aed 40%, #ec4899 60%, #7c3aed 80%, #2563eb 100%)",
  backgroundSize: "200% auto",
  backgroundPosition: "0% center",
  backgroundClip: "text",
  WebkitBackgroundClip: "text",
  color: "transparent",
  WebkitTextFillColor: "transparent",
  animation: "voicehireTextShine 4s linear infinite",
  userSelect: "none",
  filter:
    "drop-shadow(0 0 8px rgba(99,102,241,0.20)) drop-shadow(0 0 16px rgba(236,72,153,0.12))",
};

export const compactShellStyle: CSSProperties = {
  gridTemplateColumns: "1fr",
  gap: 16,
  width: "min(720px, 100%)",
};

export const compactHeroCardStyle: CSSProperties = {
  height: "auto",
  minHeight: "auto",

  alignSelf: "stretch",

  paddingTop: 56,
};

export const compactFormCardStyle: CSSProperties = {
  height: "auto",
  minHeight: "auto",
  alignSelf: "stretch",
};

export const compactHeroContentStyle: CSSProperties = {
  justifyItems: "center",
  textAlign: "center",
  width: "100%",
};

export const compactHeroListStyle: CSSProperties = {
  width: "100%",
  display: "grid",
  gap: 10,
  margin: 0,
  padding: 0,
  listStyle: "none",
};

export const compactHeroListItemStyle: CSSProperties = {
  display: "grid",
  justifyItems: "center",
  alignItems: "center",
  gap: 6,

  width: "100%",
  minHeight: 64,
  padding: "12px 14px",

  borderRadius: 18,
  border: "1px solid rgba(148, 163, 184, 0.16)",
  borderLeft: "3px solid rgba(59, 130, 246, 0.72)",
  background:
    "linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,255,0.98) 100%)",
  boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
  textAlign: "center",
};


export const compactFieldHintStyle: CSSProperties = {
  textAlign: "center",
  maxWidth: "100%",
};

export const compactMarqueeWordStyle: CSSProperties = {
  fontSize: "clamp(2.2rem, 12vw, 4.4rem)",
  letterSpacing: "0.07em",
};

export const compactLabelStyle: CSSProperties = {
  display: "grid",
  gap: 8,
  fontSize: 14,
  fontWeight: 700,
  color: "#111827",
  textAlign: "center",
  justifyItems: "center",
};

export const compactSectionTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: "clamp(1.05rem, 3.6vw, 1.25rem)",
  lineHeight: 1.2,
  color: "#0f172a",
  fontWeight: 900,
  letterSpacing: "-0.03em",
  textAlign: "center",
};

export const compactResumeHeaderStyle: CSSProperties = {
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  gap: 10,
  width: "100%",
};

export const compactFormTitleStyle: CSSProperties = {
  margin: 0,
  fontSize: "clamp(1.35rem, 4.4vw, 1.7rem)",
  lineHeight: 1.15,
  fontWeight: 900,
  letterSpacing: "-0.03em",
  color: "transparent",
  backgroundImage:
    "linear-gradient(90deg, #2563eb 0%, #4f46e5 35%, #7c3aed 72%, #d946ef 100%)",
  backgroundClip: "text",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  textAlign: "center",
  width: "100%",
};

export const compactHeroBadgeStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minWidth: 26,
  height: 26,
  padding: "0 8px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 800,
  letterSpacing: "0.08em",
  color: "#1d4ed8",
  background:
    "linear-gradient(180deg, rgba(239,244,255,0.98), rgba(226,233,255,0.98))",
  border: "1px solid rgba(99, 102, 241, 0.14)",
  boxShadow: "0 8px 18px rgba(99, 102, 241, 0.08)",
};

export const compactHeroTextStyle: CSSProperties = {
  fontSize: "0.86rem",
  fontWeight: 600,
  lineHeight: 1.35,
  color: "#334155",
  textAlign: "center",
  maxWidth: "90%",
};

export const compactSubtitleStyle: CSSProperties = {
  margin: 0,
  maxWidth: "22rem",
  fontSize: "0.95rem",
  lineHeight: 1.6,
  color: "#64748b",
  textAlign: "center",
  justifySelf: "center",
};

export const compactFormSeparatorStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr auto 1fr",
  alignItems: "center",
  gap: 12,
  marginTop: 16,
  marginBottom: 16,
  padding: "8px 0",
};