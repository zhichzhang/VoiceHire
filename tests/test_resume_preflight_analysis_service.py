from app.server.services.resume_preflight_analysis_service import (
    ResumePreflightAnalysisService,
)
from app.server.models.application_bootstrap import ResumeUpsertDecision


SEED_RESUME_TEXT = """
ZHICHENG ZHANG
Los Angeles, CA
zzhang32@usc.edu
zhichzhang.dev
github.com/zhichzhang
linkedin.com/in/zhichzhang

EDUCATION
University of Southern California
Master of Science in Computer Science
Expected May 2027

China University of Mining and Technology
Bachelor of Engineering in Electronic Information Science and Technology
Sep 2017 – Jun 2021

EXPERIENCE
Prox Shopping
Software Engineering Intern
Jan 2026 – Mar 2026

Fogsight
Software Engineering Intern
May 2025 – Aug 2025

SKILLS
Python, TypeScript, Java, C++, PostgreSQL, Kafka, Redis, Docker, AWS
""".strip()


def test_analyze_empty_resume_uses_existing():
    result = ResumePreflightAnalysisService.analyze(
        raw_resume_text="   ",
        expected_email="zzhang32@usc.edu",
    )

    assert result.decision == ResumeUpsertDecision.USE_EXISTING
    assert result.extracted_emails == []
    assert result.extracted_name is None
    assert result.matched_sections == []
    assert result.section_score == 0.0
    assert "resume text is empty" in result.reasons


def test_analyze_email_mismatch_rejects():
    result = ResumePreflightAnalysisService.analyze(
        raw_resume_text="""
            John Doe
            john.doe@example.com

            EDUCATION
            Example University

            EXPERIENCE
            Example Company

            SKILLS
            Python, SQL
        """,
        expected_email="zzhang32@usc.edu",
    )

    assert result.decision == ResumeUpsertDecision.REJECT_MISMATCH
    assert "john.doe@example.com" in result.extracted_emails
    assert result.extracted_name == "John Doe"
    assert result.section_score > 0
    assert "resume contains a different email" in result.reasons


def test_analyze_seed_resume_passes_preflight():
    result = ResumePreflightAnalysisService.analyze(
        raw_resume_text=SEED_RESUME_TEXT,
        expected_email="zzhang32@usc.edu",
    )

    assert result.decision == ResumeUpsertDecision.NORMALIZE_UPDATE
    assert "zzhang32@usc.edu" in result.extracted_emails
    assert result.extracted_name == "ZHICHENG ZHANG"
    assert "education" in result.matched_sections
    assert "experience" in result.matched_sections
    assert "skills" in result.matched_sections
    assert result.section_score == 1.0
    assert "resume passed preflight checks" in result.reasons