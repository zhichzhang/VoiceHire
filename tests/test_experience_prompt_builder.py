from app.server.interview.coverage.coverage import CoverageResult
from app.server.llm.builders.experience_prompt_builders import ExperiencePromptBuilder
from app.server.llm.contracts.prompt_inputs import (
    ExperienceExtractionPromptInput,
    ExperienceQuestionPromptInput,
)
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume, ResumeExperience


def test_build_experience_extraction_prompt_returns_string():
    prompt = ExperiencePromptBuilder.build_extraction_prompt(
        ExperienceExtractionPromptInput(
            answer="I built a deterministic email attribution system.",
            candidate_profile=CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            resume_context=CandidateResume(
                experiences=[
                    ResumeExperience(
                        name="Deterministic Email Attribution System",
                        organization="Prox Shopping",
                        experience_type="internship",
                        timeframe="2026-01 to 2026-03",
                        summary="Built deterministic tracking systems",
                        skills=["FastAPI", "PostgreSQL"],
                    )
                ],
                skills=["backend systems", "distributed systems"],
            ),
            experience_context="Prox Shopping internship",
        )
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "structured information extraction engine" in prompt
    assert "Return JSON only" in prompt


def test_build_experience_question_prompt_collection_returns_string():
    prompt = ExperiencePromptBuilder.build_question_prompt(
        ExperienceQuestionPromptInput(
            mode="collection",
            candidate_profile=CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            experience_evidence=ExperienceEvidence(
                experience_name="Deterministic Email Attribution System",
                what="Designed a deterministic email attribution system",
                why="Improve tracking reliability",
            ),
            coverage=CoverageResult(
                score=0.5,
                complete=False,
                covered_fields=["experience_name", "what", "why"],
                missing_fields=["how", "challenge", "outcome"],
            ),
            previous_questions=["Tell me about the system."],
            previous_answers=["I built it at Prox Shopping."],
        )
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "interview workflow engine" in prompt
    assert "VALID TARGET FIELDS" in prompt
    assert "Only use fields from the list above" in prompt


def test_build_experience_question_prompt_deep_dive_returns_string():
    prompt = ExperiencePromptBuilder.build_question_prompt(
        ExperienceQuestionPromptInput(
            mode="deep_dive",
            candidate_profile=CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            experience_evidence=ExperienceEvidence(
                experience_name="Deterministic Email Attribution System",
                what="Designed a deterministic email attribution system",
                why="Improve tracking reliability",
                how="Used PostgreSQL and FastAPI",
                challenge="Retries",
                outcome="Improved accuracy",
            ),
            dimensions=["problem_solving", "ownership"],
            previous_questions=["How did you build it?"],
            previous_answers=["With PostgreSQL and Redis."],
        )
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Experience Deep Dive mode" in prompt
    assert "CURRENT EVALUATION DIMENSIONS" in prompt
    assert "QUESTION GENERATION STRATEGY" in prompt
    assert "How did you build it?" in prompt