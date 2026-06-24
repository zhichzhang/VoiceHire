import {useState, type FormEvent, useEffect} from "react";
import { useNavigate } from "react-router-dom";

import { bootstrapInterview, resumeInterview } from "../../api/interviewApi";
import { useInterviewStore } from "../../store/interviewStore";

import {
  buttonStyle,
  compactFieldHintStyle,
  compactFormCardStyle,
  compactHeroCardStyle,
  compactHeroContentStyle,
  compactHeroListItemStyle,
  compactHeroListStyle,
  compactMarqueeWordStyle,
  compactShellStyle,
  disabledButtonStyle,
  errorStyle,
  fieldHintStyle,
  formCardStyle,
  formSeparatorLineStyle,
  formSeparatorPillStyle,
  formSeparatorStyle,
  formTitleStyle,
  heroCardStyle,
  heroContentStyle,
  heroListItemStyle,
  heroListStyle,
  heroMarqueeStyle,
  heroMarqueeWordStyle,
  heroTopStyle,
  inputRowStyle,
  inputStyle,
  labelStyle,
  modalActionsStyle,
  modalCardStyle,
  modalMessageStyle,
  modalOkButtonStyle,
  modalOverlayStyle,
  modalTitleStyle,
  noteStyle,
  pageStyle,
  resumeHeaderStyle,
  resumeIconStyle,
  secondaryButtonStyle,
  sectionStackStyle,
  sectionTitleStyle,
  sessionInputStyle,
  shellStyle,
  subtitleStyle,
  textareaStyle,
  compactHeroBadgeStyle,
  compactHeroTextStyle,
  compactLabelStyle,
  compactFormTitleStyle,
  compactResumeHeaderStyle,
  compactSectionTitleStyle, compactSubtitleStyle, compactFormSeparatorStyle,
} from "./landingPage.styles";

const highlights = [
  "AI-powered voice interviews",
  "Resume-aware follow-up questions",
  "Automated evaluation and reporting",
];

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function isValidSessionId(value: string): boolean {
  return UUID_PATTERN.test(value.trim());
}

function getResumeErrorMessage(err: unknown): string {
  const message = err instanceof Error ? err.message : "";

  if (
    /not found/i.test(message) ||
    /404/i.test(message) ||
    /session not found/i.test(message)
  ) {
    return "This session could not be found. Please check the Session ID and try again.";
  }

  if (/failed to fetch/i.test(message)) {
    return "Could not reach the server. Please make sure the backend is running and try again.";
  }

  return message || "Failed to resume this session. Please try again later.";
}

function getBootstrapErrorMessage(err: unknown): string {
  const message = err instanceof Error ? err.message : "";

  if (/failed to fetch/i.test(message)) {
    return "Could not reach the server. Please make sure the backend is running and try again.";
  }

  if (/resume/i.test(message) && /reject|mismatch|preflight/i.test(message)) {
    return message;
  }

  return message || "Failed to start interview.";
}

type DialogState = {
  title: string;
  message: string;
} | null;

export default function LandingPage() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [resumeSessionId, setResumeSessionId] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [dialog, setDialog] = useState<DialogState>(null);
  const [windowWidth, setWindowWidth] = useState<number>(() =>
  typeof window !== "undefined" ? window.innerWidth : 1200,
);

  const isCompact = windowWidth <= 900;

  const shellStyleToUse = isCompact ? compactShellStyle : shellStyle;
  const heroCardStyleToUse = isCompact ? compactHeroCardStyle : heroCardStyle;
  const formCardStyleToUse = isCompact ? compactFormCardStyle : formCardStyle;
  const heroContentStyleToUse = isCompact
    ? compactHeroContentStyle
    : heroContentStyle;
  const heroListStyleToUse = isCompact ? compactHeroListStyle : heroListStyle;
  const heroListItemStyleToUse = isCompact
    ? compactHeroListItemStyle
    : heroListItemStyle;
  const fieldHintStyleToUse = isCompact ? compactFieldHintStyle : fieldHintStyle;
  const marqueeWordStyleToUse = isCompact
    ? { ...heroMarqueeWordStyle, ...compactMarqueeWordStyle }
  : heroMarqueeWordStyle;
  const subtitleStyleToUse = isCompact
  ? compactSubtitleStyle
  : subtitleStyle;

  const labelStyleToUse = isCompact
    ? compactLabelStyle
    : labelStyle;

  const formTitleStyleToUse = isCompact
    ? compactFormTitleStyle
    : formTitleStyle;

  const resumeHeaderStyleToUse = isCompact
    ? compactResumeHeaderStyle
    : resumeHeaderStyle;

  const sectionTitleStyleToUse = isCompact
    ? compactSectionTitleStyle
    : sectionTitleStyle;

  const formSeparatorStyleToUse = isCompact
  ? compactFormSeparatorStyle
  : formSeparatorStyle;

  const trimmedName = name.trim();
  const trimmedEmail = email.trim();
  const trimmedResumeText = resumeText.trim();
  const trimmedSessionId = resumeSessionId.trim();

  const canCreate =
    !isLoading && trimmedName.length > 0 && trimmedEmail.length > 0;

  const canResume = !isLoading && isValidSessionId(trimmedSessionId);

  const closeDialog = () => setDialog(null);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!canCreate) {
      return;
    }

    setInlineError(null);
    setDialog(null);
    setIsLoading(true);

    try {
      const payload = await bootstrapInterview({
        email: trimmedEmail,
        name: trimmedName,
        raw_resume_text: trimmedResumeText,
      });

      useInterviewStore.getState().setBootstrapState(
        payload,
        trimmedResumeText,
      );

      navigate(
        `/session/${payload.session.session_id}/loading?next=interview&restore=0`,
        { replace: true },
      );
    } catch (err) {
      setDialog({
        title: "Cannot start interview",
        message: getBootstrapErrorMessage(err),
      });
    } finally {
      setIsLoading(false);
    }
  };

  const onResume = async () => {
    if (!canResume) {
      return;
    }

    setInlineError(null);
    setDialog(null);
    setIsLoading(true);

    try {
      const payload = await resumeInterview({
        session_id: trimmedSessionId,
      });

      useInterviewStore.getState().setSessionState(payload.session);

      navigate(
        `/session/${payload.session.session_id}/loading?next=interview&restore=0`,
        { replace: true },
      );
    } catch (err) {
      setDialog({
        title: "Cannot resume interview",
        message: getResumeErrorMessage(err),
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
  <div style={pageStyle}>
    <style>{`
      @keyframes voicehireTextShine {
        0% {
          background-position: 0% center;
        }
        100% {
          background-position: 200% center;
        }
      }
    `}</style>

    <div style={shellStyleToUse}>
      <section style={heroCardStyleToUse}>
        <div style={heroTopStyle} />

        <div style={heroContentStyleToUse}>
          <div style={heroMarqueeStyle}>
            <span style={marqueeWordStyleToUse}>VOICEHIRE</span>
          </div>

          <p style={subtitleStyleToUse}>
            Fill and click to practice real interviews with AI.
          </p>
        </div>

        <ul style={heroListStyleToUse}>
  {highlights.map((item, index) => (
    <li key={item} style={heroListItemStyleToUse}>
      {isCompact ? (
        <>
          <span style={compactHeroBadgeStyle}>
            {String(index + 1).padStart(2, "0")}
          </span>

          <span style={compactHeroTextStyle}>
            {item}
          </span>
        </>
      ) : (
        item
      )}
    </li>
  ))}
</ul>

        <p style={fieldHintStyleToUse}>
          Start a new session or resume an existing one with a Session ID.
        </p>
      </section>

      <section style={formCardStyleToUse}>
        <div style={sectionStackStyle}>
          <h2 style={formTitleStyleToUse}>Create a New Interview Session</h2>

          <form onSubmit={onSubmit} style={inputRowStyle}>
            <label style={labelStyleToUse}>
              Name
              <input
                style={inputStyle}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                autoComplete="name"
                required
              />
            </label>

            <label style={labelStyleToUse}>
              Email
              <input
                style={inputStyle}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                autoComplete="email"
                required
              />
            </label>

            <label style={labelStyleToUse}>
              Resume Text (Optional)
              <textarea
                style={textareaStyle}
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste your resume here (optional)..."
                spellCheck={false}
              />
            </label>

            <p style={noteStyle}>
              If you leave this blank, VoiceHire will try to use a stored
              resume for the same email. If none exists, you will see a clear
              error popup after clicking Start Interview.
            </p>

            {inlineError ? <p style={errorStyle}>{inlineError}</p> : null}

            <button
              type="submit"
              style={{
                ...buttonStyle,
                ...(!canCreate ? disabledButtonStyle : null),
              }}
              disabled={!canCreate}
            >
              {isLoading ? "Starting..." : "Start Interview"}
            </button>
          </form>
        </div>

        <div style={formSeparatorStyleToUse}>
          <div style={formSeparatorLineStyle} />
          <span style={formSeparatorPillStyle}>OR</span>
          <div style={formSeparatorLineStyle} />
        </div>

        <div style={sectionStackStyle}>
          <div style={resumeHeaderStyleToUse}>
            <div style={resumeIconStyle}>▶</div>
            <h2 style={sectionTitleStyleToUse}>Resume Existing Interview</h2>
          </div>

          <label style={labelStyleToUse}>
            Session ID
            <input
              style={sessionInputStyle}
              value={resumeSessionId}
              onChange={(e) => setResumeSessionId(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              autoComplete="off"
              spellCheck={false}
              inputMode="text"
              maxLength={64}
            />
          </label>

          <p style={noteStyle}>
            Paste the generated Session ID to resume an existing interview.
          </p>

          <button
            type="button"
            style={{
              ...secondaryButtonStyle,
              ...(!canResume ? disabledButtonStyle : null),
            }}
            disabled={!canResume}
            onClick={() => void onResume()}
          >
            Resume Interview
          </button>
        </div>
      </section>
    </div>

    {dialog ? (
      <div onClick={closeDialog} style={modalOverlayStyle}>
        <div onClick={(e) => e.stopPropagation()} style={modalCardStyle}>
          <h3 style={modalTitleStyle}>{dialog.title}</h3>
          <p style={modalMessageStyle}>{dialog.message}</p>
          <div style={modalActionsStyle}>
            <button
              type="button"
              onClick={closeDialog}
              style={modalOkButtonStyle}
            >
              OK
            </button>
          </div>
        </div>
      </div>
    ) : null}
  </div>
);
}
