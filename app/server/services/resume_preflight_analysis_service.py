# app/server/interview/services/resume_preflight_analysis_service.py

from __future__ import annotations

import re

from app.server.models.application_bootstrap import ResumeUpsertDecision, ResumePreflightResult

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

SECTION_KEYWORDS = {
    "contact": ["contact", "contact information", "personal information", "info", "email", "phone", "address", "linkedin", "github", "portfolio", "website"],
    "summary": ["summary", "professional summary", "profile", "about me", "objective", "career objective", "personal summary"],
    "education": ["education", "academic background", "academics", "educational background", "academic history", "schooling", "qualifications", "coursework", "relevant coursework", "study"],
    "experience": ["experience", "work experience", "professional experience", "employment", "employment history", "work history", "professional background", "career history", "internship", "internships", "full-time", "full time"],
    "skills": ["skills", "technical skills", "technologies", "tooling", "tools", "competencies", "core competencies", "technical competencies", "stack", "tech stack", "languages", "programming languages"],
    "projects": ["projects", "project experience", "personal projects", "academic projects", "side projects", "selected projects", "featured projects"],
    "research": ["research", "research experience", "research projects", "research interests", "lab experience"],
    "publications": ["publications", "publication", "papers", "journal", "conference", "article"],
    "certifications": ["certifications", "certification", "licenses", "licences", "credential", "credentials"],
    "awards": ["awards", "honors", "honours", "distinctions", "scholarships", "achievements"],
    "leadership": ["leadership", "leadership experience", "extracurricular", "activities", "student activities", "organization involvement", "club", "student club"],
    "volunteering": ["volunteering", "volunteer experience", "community service", "service"],
    "languages": ["languages", "spoken languages", "language skills"],
    "interests": ["interests", "hobbies", "additional information", "other information"],
}

CORE_SECTIONS = {"education", "experience", "skills"}
MIN_CORE_MATCHES = 2


class ResumePreflightAnalysisService:
    @staticmethod
    def analyze(
        raw_resume_text: str,
        expected_email: str,
    ) -> ResumePreflightResult:
        text = raw_resume_text.strip()
        if not text:
            return ResumePreflightResult(
                decision=ResumeUpsertDecision.USE_EXISTING,
                extracted_emails=[],
                extracted_name=None,
                matched_sections=[],
                section_score=0.0,
                reasons=["resume text is empty"],
            )

        normalized_text = ResumePreflightAnalysisService._normalize_text(text)
        extracted_emails = EMAIL_RE.findall(text)
        normalized_expected_email = expected_email.strip().casefold()

        # 1) email mismatch -> reject immediately
        if extracted_emails:
            normalized_emails = {
                e.strip().casefold() for e in extracted_emails
            }
            if normalized_expected_email not in normalized_emails:
                matched_sections = ResumePreflightAnalysisService._detect_sections(
                    normalized_text
                )
                return ResumePreflightResult(
                    decision=ResumeUpsertDecision.REJECT_MISMATCH,
                    extracted_emails=extracted_emails,
                    extracted_name=ResumePreflightAnalysisService._extract_name(text),
                    matched_sections=matched_sections,
                    section_score=ResumePreflightAnalysisService._section_score(matched_sections),
                    reasons=["resume contains a different email"],
                )

        # 2) section keyword check
        matched_sections = ResumePreflightAnalysisService._detect_sections(
            normalized_text
        )
        section_score = ResumePreflightAnalysisService._section_score(matched_sections)

        if ResumePreflightAnalysisService._core_matches(matched_sections) < MIN_CORE_MATCHES:
            return ResumePreflightResult(
                decision=ResumeUpsertDecision.REJECT_MISMATCH,
                extracted_emails=extracted_emails,
                extracted_name=ResumePreflightAnalysisService._extract_name(text),
                matched_sections=matched_sections,
                section_score=section_score,
                reasons=[
                    "resume does not look like a resume",
                    "too few core section keywords matched",
                ],
            )

        return ResumePreflightResult(
            decision=ResumeUpsertDecision.NORMALIZE_UPDATE,
            extracted_emails=extracted_emails,
            extracted_name=ResumePreflightAnalysisService._extract_name(text),
            matched_sections=matched_sections,
            section_score=section_score,
            reasons=["resume passed preflight checks"],
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).casefold()

    @staticmethod
    def _extract_name(text: str) -> str | None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return None

        first_line = lines[0]
        if EMAIL_RE.search(first_line):
            return None

        if len(first_line) <= 80:
            return first_line

        return None

    @staticmethod
    def _detect_sections(normalized_text: str) -> list[str]:
        matched: list[str] = []

        for section_name, keywords in SECTION_KEYWORDS.items():
            if any(keyword.casefold() in normalized_text for keyword in keywords):
                matched.append(section_name)

        return matched

    @staticmethod
    def _core_matches(matched_sections: list[str]) -> int:
        return sum(1 for section in matched_sections if section in CORE_SECTIONS)

    @staticmethod
    def _section_score(
            matched_sections: list[str],
    ) -> float:

        if not CORE_SECTIONS:
            return 0.0

        matched_core = [
            section
            for section in matched_sections
            if section in CORE_SECTIONS
        ]

        return len(matched_core) / len(CORE_SECTIONS)