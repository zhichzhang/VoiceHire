# tests/test_intro_prompt_builder.py

from app.server.interview.coverage.coverage import CoverageResult
from app.server.llm.builders.intro_prompt_builders import (
    IntroPromptBuilder,
)
from app.server.llm.contracts.prompt_inputs import (
    IntroExtractionPromptInput,
    IntroQuestionPromptInput,
)
from app.server.models.candidate import CandidateProfile
from app.server.models.resume import (
    CandidateResume,
    ResumeEducation,
    ResumeExperience,
)


def test_build_intro_extraction_prompt_returns_string():
    prompt = IntroPromptBuilder.build_extraction_prompt(
        IntroExtractionPromptInput(
            answer=(
                "I'm a software engineering intern at Prox Shopping "
                "and I study CS at USC."
            ),
            resume_context=CandidateResume(
                education=[
                    ResumeEducation(
                        institution="USC",
                        program="Computer Science",
                        status="current student",
                    )
                ],
                experiences=[
                    ResumeExperience(
                        name="Software Engineer Intern",
                        organization="Prox Shopping",
                        experience_type="internship",
                        timeframe="2026-01 to 2026-03",
                        summary="Built deterministic tracking systems",
                        skills=["FastAPI", "PostgreSQL"],
                    )
                ],
                skills=["backend systems", "distributed systems"],
            ),
            current_profile=CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
        )
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0

    # template itself should always be present
    assert "structured information extraction engine" in prompt


def test_build_intro_question_prompt_returns_string():
    prompt = IntroPromptBuilder.build_question_prompt(
        IntroQuestionPromptInput(
            candidate_profile=CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            coverage=CoverageResult(
                score=0.2,
                complete=False,
                covered_fields=["most_recent_role"],
                missing_fields=["education"],
            ),
            previous_questions=[
                "Please introduce yourself."
            ],
            previous_answers=[
                "I am a software engineering intern."
            ],
        )
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0

    assert "interview workflow engine" in prompt
    assert "VALID TARGET FIELDS" in prompt