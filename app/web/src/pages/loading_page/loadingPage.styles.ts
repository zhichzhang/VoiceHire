import type { CSSProperties } from "react";

export const pageStyle: CSSProperties = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  padding: 24,

  background:
    "radial-gradient(circle at 14% 12%, rgba(255,255,255,0.98) 0%, rgba(250,252,255,1) 34%, rgba(240,244,255,1) 100%)",
};

export const cardStyle: CSSProperties = {
  width: "min(520px, 100%)",

  padding: "42px 36px",

  borderRadius: 30,

  border: "1px solid rgba(148,163,184,0.18)",

  background:
    "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(253,253,255,0.98) 100%)",

  boxShadow: "0 18px 46px rgba(15,23,42,0.08)",

  display: "grid",

  justifyItems: "center",

  gap: 18,

  textAlign: "center",
};

export const logoStyle: CSSProperties = {
  fontSize: "clamp(2.4rem, 5vw, 3.6rem)",

  fontWeight: 900,

  letterSpacing: "0.1em",

  textTransform: "uppercase",

  backgroundImage:
    "linear-gradient(90deg,#2563eb 0%,#4f46e5 30%,#7c3aed 60%,#ec4899 100%)",

  backgroundClip: "text",
  WebkitBackgroundClip: "text",

  color: "transparent",
  WebkitTextFillColor: "transparent",

  margin: 0,
};

export const spinnerStyle: CSSProperties = {
  width: 56,
  height: 56,

  borderRadius: "50%",

  border: "5px solid rgba(99,102,241,0.15)",

  borderTopColor: "#2563eb",

  borderRightColor: "#7c3aed",

  animation: "spin 1s linear infinite",
};

export const titleStyle: CSSProperties = {
  margin: 0,

  fontSize: 28,

  fontWeight: 900,

  lineHeight: 1.15,

  letterSpacing: "-0.03em",

  color: "#0f172a",
};

export const textStyle: CSSProperties = {
  margin: 0,

  color: "#546075",

  fontSize: 16,

  lineHeight: 1.8,
};

export const hintStyle: CSSProperties = {
  margin: 0,
  color: "#64748b",
  fontSize: 13,
  lineHeight: 1.5,
};

export const noticeStyle: CSSProperties = {
  width: "100%",
  margin: "0 0 6px",
  padding: "12px 14px",
  borderRadius: 14,
  background: "#fff7ed",
  border: "1px solid rgba(249, 115, 22, 0.18)",
  color: "#9a3412",
  fontSize: 14,
  lineHeight: 1.55,
  textAlign: "left",
};

export const errorStyle: CSSProperties = {
  margin: 0,
  color: "#b00020",
  fontSize: 14,
  lineHeight: 1.6,
};

export const buttonStyle: CSSProperties = {
  width: "100%",

  padding: "14px 18px",

  borderRadius: 16,

  border: "none",

  background:
    "linear-gradient(90deg,#2563eb 0%,#4f46e5 35%,#7c3aed 70%,#d946ef 100%)",

  color: "white",

  fontWeight: 800,

  fontSize: 16,

  cursor: "pointer",

  boxShadow: "0 14px 30px rgba(76,81,191,0.18)",
};