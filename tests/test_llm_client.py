import pytest

from app.server.interview.coverage.coverage import CoverageResult
from app.server.llm.client import LLMClient
from app.server.llm.contracts.prompt_inputs import (
    ExperienceExtractionPromptInput,
    ExperienceQuestionPromptInput,
    IntroExtractionPromptInput,
    IntroQuestionPromptInput,
)
from app.server.llm.contracts.prompt_outputs import (
    ExperienceExtractionResult,
    InterviewFeedbackResult,
    IntroExtractionResult,
    PhaseEvaluationResult,
    QuestionGenerationResult,
)
from app.server.llm.providers.mock import MockLLMProvider
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence
from app.server.models.resume import CandidateResume, ResumeEducation, ResumeExperience


@pytest.mark.asyncio
async def test_raw_invoke_returns_string_when_no_response_model():
    provider = MockLLMProvider(response="raw text response")
    llm = LLMClient(provider=provider)

    result = await llm.invoke("hello")

    assert result == "raw text response"
    assert provider.calls
    assert provider.calls[0]["prompt"] == "hello"


@pytest.mark.asyncio
async def test_intro_extraction():
    provider = MockLLMProvider(
        response={
            "most_recent_role": "Software Engineer Intern",
            "education": {
                "institution": "USC",
                "program": "Computer Science",
                "status": "current student",
            },
            "highlighted_experiences": [
                {
                    "organization": "Prox Shopping",
                    "timeframe": "2026-01 to 2026-03",
                    "summary": "Built deterministic tracking systems",
                    "responsibilities": ["Designed click tracking"],
                    "achievements": ["Improved attribution accuracy"],
                }
            ],
            "domain_keywords": ["backend systems", "distributed systems"],
            "other_context": ["Interested in scalable systems"],
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.extract_intro(
        IntroExtractionPromptInput(
            answer=(
                "I'm a software engineering intern at Prox Shopping "
                "and a CS master's student at USC."
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
            current_profile=CandidateProfile(),
        )
    )

    assert isinstance(result, IntroExtractionResult)
    assert result.most_recent_role == "Software Engineer Intern"
    assert result.education is not None
    assert result.education.institution == "USC"
    assert result.domain_keywords == ["backend systems", "distributed systems"]

    assert provider.calls
    assert provider.calls[0]["response_model"] is IntroExtractionResult


@pytest.mark.asyncio
async def test_intro_question_generation():
    provider = MockLLMProvider(
        response={
            "phase": "intro",
            "question": "Can you tell me more about your educational background?",
            "target_fields": ["education"],
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.generate_intro_question(
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
            previous_questions=["Please introduce yourself."],
            previous_answers=["I am a software engineering intern."],
        )
    )

    assert isinstance(result, QuestionGenerationResult)
    assert result.phase == "intro"
    assert result.target_fields == ["education"]
    assert "educational background" in result.question

    assert provider.calls
    assert provider.calls[0]["response_model"] is QuestionGenerationResult


@pytest.mark.asyncio
async def test_experience_extraction():
    provider = MockLLMProvider(
        response={
            "experience_type": "internship",
            "experience_name": "Deterministic Email Attribution System",
            "what": "Designed a deterministic email attribution system",
            "why": "Improve tracking reliability",
            "how": "Used PostgreSQL, FastAPI, and append-only event logs",
            "challenge": "Maintaining consistency under retries",
            "outcome": "Improved attribution accuracy",
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.extract_experience(
        ExperienceExtractionPromptInput(
            answer=(
                "I designed a deterministic email attribution system using "
                "PostgreSQL and FastAPI."
            ),
            candidate_profile=CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            resume_context=CandidateResume(skills=["PostgreSQL", "FastAPI"]),
            experience_context="Prox Shopping internship",
        )
    )

    assert isinstance(result, ExperienceExtractionResult)
    assert result.experience_type == "internship"
    assert result.experience_name == "Deterministic Email Attribution System"
    assert result.what == "Designed a deterministic email attribution system"

    assert provider.calls
    assert provider.calls[0]["response_model"] is ExperienceExtractionResult


@pytest.mark.asyncio
async def test_experience_question_generation_collection():
    provider = MockLLMProvider(
        response={
            "phase": "experience",
            "question": "What was the biggest challenge you encountered?",
            "target_fields": ["challenge"],
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.generate_experience_question(
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

    assert isinstance(result, QuestionGenerationResult)
    assert result.phase == "experience"
    assert result.target_fields == ["challenge"]
    assert "challenge" in result.question

    assert provider.calls
    assert provider.calls[0]["response_model"] is QuestionGenerationResult


@pytest.mark.asyncio
async def test_experience_question_generation_deep_dive():
    provider = MockLLMProvider(
        response={
            "phase": "experience",
            "question": "What alternative approaches did you consider?",
            "target_fields": [],
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.generate_experience_deep_dive_question(
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
                how="Used PostgreSQL and FastAPI",
                challenge="Retries",
                outcome="Improved accuracy",
            ),
            previous_questions=["How did you build it?"],
            previous_answers=["With PostgreSQL and Redis."],
        )
    )

    assert isinstance(result, QuestionGenerationResult)
    assert result.phase == "experience"
    assert "alternative approaches" in result.question

    assert provider.calls
    assert provider.calls[0]["response_model"] is QuestionGenerationResult


@pytest.mark.asyncio
async def test_phase_evaluation():
    provider = MockLLMProvider(
        response={
            "phase_name": "intro",
            "dimensions": [
                {
                    "name": "relevance",
                    "score": 85,
                    "justification": "Answer addressed the question directly.",
                }
            ],
            "overall_score": 85,
            "strengths": ["Clear background summary"],
            "improvements": ["Provide more detail on education"],
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.evaluate_phase(
        {
            "phase_name": "intro",
            "rubric": "intro rubric",
            "candidate_profile": CandidateProfile(
                most_recent_role="Software Engineer Intern",
            ),
            "experience_evidence": ExperienceEvidence(),
            "communication_metrics": {
                "relevance": 0.8,
                "clarity": 0.9,
                "fluency": 0.85,
            },
            "dimensions": ["relevance", "clarity", "fluency"],
        }
    )

    assert isinstance(result, PhaseEvaluationResult)
    assert result.phase_name == "intro"
    assert result.overall_score == 85
    assert result.dimensions[0].name == "relevance"

    assert provider.calls
    assert provider.calls[0]["response_model"] is PhaseEvaluationResult


@pytest.mark.asyncio
async def test_final_evaluation():
    provider = MockLLMProvider(
        response={
            "phase_results": [
                {
                    "phase_name": "intro",
                    "dimensions": [
                        {
                            "name": "relevance",
                            "score": 85,
                            "justification": "Good intro coverage.",
                        }
                    ],
                    "overall_score": 85,
                    "strengths": ["Clear background summary"],
                    "improvements": ["Expand on technical depth"],
                }
            ],
            "communication_score": 88,
            "professional_score": 90,
            "overall_score": 89,
            "assessment_confidence": 0.92,
            "strengths": ["Strong communication"],
            "improvements": ["More quantitative impact metrics"],
        }
    )

    llm = LLMClient(provider=provider)

    result = await llm.generate_final_evaluation(
        {
            "candidate_profile": CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            "experience_evidence": ExperienceEvidence(
                experience_name="Deterministic Email Attribution System",
            ),
            "phase_evaluations": [
                {
                    "phase_name": "intro",
                    "overall_score": 85,
                }
            ],
            "communication_metrics": {
                "relevance": 0.8,
                "clarity": 0.9,
                "fluency": 0.85,
            },
            "interview_evaluation": {
                "phase_results": [],
                "communication_score": 88,
                "professional_score": 90,
                "overall_score": 89,
                "assessment_confidence": 0.92,
                "strengths": ["Strong communication"],
                "improvements": ["More quantitative impact metrics"],
            },
        }
    )

    assert isinstance(result, InterviewFeedbackResult)
    assert result.overall_score == 89
    assert result.assessment_confidence == 0.92
    assert result.phase_results[0].phase_name == "intro"

    assert provider.calls
    assert provider.calls[0]["response_model"] is InterviewFeedbackResult