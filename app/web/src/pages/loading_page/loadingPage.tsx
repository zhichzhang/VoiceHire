// app/web/src/pages/loading_page/loadingPage.tsx

import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { getInterviewSession } from "../../api/interviewApi";
import { useInterviewStore } from "../../store/interviewStore";

import {
  pageStyle,
  cardStyle,
  spinnerStyle,
  titleStyle,
  textStyle,
  errorStyle,
  buttonStyle,
  hintStyle,
  noticeStyle, logoStyle,
} from "./loadingPage.styles";

type LoadingLocationState = {
  resumeNotice?: string;
};

export default function LoadingPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const setSessionState = useInterviewStore.getState().setSessionState;
  const setError = useInterviewStore.getState().setError;

  const [localError, setLocalError] = useState<string | null>(null);

  const missingSessionId = !sessionId;
  const resumeNotice =
    (location.state as LoadingLocationState | null | undefined)?.resumeNotice ??
    null;

  useEffect(() => {
  if (missingSessionId || !sessionId) {
    return;
  }

  let cancelled = false;

  const searchParams = new URLSearchParams(location.search);
  const next = searchParams.get("next") ?? "interview";
  const restore = searchParams.get("restore") === "1";

  const target =
    next === "evaluation"
      ? `/session/${sessionId}/evaluation`
      : `/session/${sessionId}`;

  const loadSession = async () => {
    try {
      if (restore) {
        const payload = await getInterviewSession(sessionId);
        if (cancelled) {
          return;
        }
        setSessionState(payload.session);
      }

      if (cancelled) {
        return;
      }

      navigate(target, {
        replace: true,
      });
    } catch (err) {
      if (cancelled) {
        return;
      }

      const message =
        err instanceof Error ? err.message : "Failed to load session.";

      setLocalError(message);
      setError(message);
    }
  };

  void loadSession();

  return () => {
    cancelled = true;
  };
}, [
  location.search,
  missingSessionId,
  navigate,
  sessionId,
  setError,
  setSessionState,
]);

  if (missingSessionId) {
    return (
      <div style={pageStyle}>
        <div style={cardStyle}>
          <h2 style={titleStyle}>Missing session id</h2>

          <button
            type="button"
            style={buttonStyle}
            onClick={() => navigate("/")}
          >
            Back to landing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        {localError ? (
          <>
            <h2 style={titleStyle}>Failed to load session</h2>

            <p style={errorStyle}>{localError}</p>

            <button
              type="button"
              style={buttonStyle}
              onClick={() => navigate("/")}
            >
              Back to landing
            </button>
          </>
        ) : (
          <>
            {resumeNotice ? (
              <div style={noticeStyle}>{resumeNotice}</div>
            ) : null}
            <h1 style={logoStyle}>VOICEHIRE</h1>

            <div style={spinnerStyle} />

            <h2 style={titleStyle}>Loading...</h2>

            <p style={textStyle}>
              Please wait while we prepare the next screen.
            </p>

            <p style={hintStyle}>
              This usually takes only a few seconds.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
