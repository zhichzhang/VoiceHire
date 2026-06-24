import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import LandingPage from "./pages/landing_page/landingPage";
import InterviewPage from "./pages/interview_page/InterviewPage";
import EvaluationPage from "./pages/evaluation_page/EvaluationPage";
import DevAudioPageLivekit from "./pages/dev_audio_page/DevAudioPage.livekit.tsx";
import LoadingPage from "./pages/loading_page/loadingPage.tsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
          <Route path="/dev/audio" element={<DevAudioPageLivekit />}/>
        <Route path="/session/:sessionId/loading" element={<LoadingPage />} />
        <Route path="/session/:sessionId" element={<InterviewPage />} />
        <Route path="/session/:sessionId/evaluation" element={<EvaluationPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

