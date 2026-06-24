import {
  compactHintStyle,
  footerRowStyle,
  pausedPillStyle,
  recordingPillStyle,
  recorderBadgeStyle,
  recorderCardStyle,
  recorderHeaderStyle,
  recorderSubtitleStyle,
  recorderTitleStyle,
  statusTextPillStyle,
  transcriptBoxStyle,
  waveformBarStyle,
  waveformRowStyle,
} from "./InterviewAnswerRecorder.styles";

type InterviewAnswerRecorderProps = {
  transcript: string;
  isFinal: boolean;
  audioLevel: number; // 0 ~ 1
  micEnabled: boolean;
  statusText?: string;
  title?: string;
  placeholder?: string;
};

function clamp(value: number, min = 0, max = 1): number {
  return Math.min(max, Math.max(min, value));
}

export function InterviewAnswerRecorder({
  transcript,
  isFinal,
  audioLevel,
  micEnabled,
  statusText,
  title = "Live transcript",
  placeholder = "Waiting for speech...",
}: InterviewAnswerRecorderProps) {
  const level = clamp(audioLevel);

  const bars = Array.from({ length: 14 }, (_, index) => {
    const spread = 0.55 + (index % 5) * 0.1;
    const height = Math.max(10, 10 + Math.round(level * 72 * spread));
    return height;
  });

  return (
    <section style={recorderCardStyle}>
      <div style={recorderHeaderStyle}>
        <div>
          <h3 style={recorderTitleStyle}>{title}</h3>
          <div style={recorderSubtitleStyle}>
            {statusText ?? (micEnabled ? "Recording" : "Paused")}
          </div>
        </div>

        <div
            style={{
              ...recorderBadgeStyle,
              opacity: micEnabled ? 1 : 0.55,
            }}
          >
          {isFinal ? "final" : "interim"}
        </div>
      </div>

      <div style={transcriptBoxStyle}>
        {transcript.trim() ? transcript : placeholder}
      </div>

      <div style={waveformRowStyle} aria-hidden="true">
        {bars.map((height, index) => (
          <span
            key={index}
            style={{
              ...waveformBarStyle,
              height,
              opacity: micEnabled ? 1 : 0.28,
            }}
          />
        ))}
      </div>

      <div style={footerRowStyle}>
        <span style={micEnabled ? recordingPillStyle : pausedPillStyle}>
          {micEnabled ? "Recording" : "Paused"}
        </span>
        <span style={statusTextPillStyle}>{isFinal ? "final" : "interim"}</span>
        {statusText ? <span>{statusText}</span> : null}
      </div>

      <p style={compactHintStyle}>
        The recorder shows only the current answer. Pause or Next will capture the
        transcript, submit it to the interview workflow, and clear the buffer for
        the next turn.
      </p>
    </section>
  );
}
