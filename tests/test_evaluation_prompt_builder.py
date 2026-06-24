from app.server.llm.builders.evaluation_prompt_builders import EvaluationPromptBuilder
from app.server.models.candidate import CandidateProfile
from app.server.models.experience_evidence import ExperienceEvidence


def test_build_evaluation_prompt_returns_string():
    prompt = EvaluationPromptBuilder.build_evaluation_prompt(
        {
            "phase_name": "intro",
            "rubric": "intro rubric",
            "candidate_profile": CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            "experience_evidence": ExperienceEvidence(
                experience_name="Deterministic Email Attribution System",
                what="Designed a deterministic email attribution system",
            ),
            "communication_metrics": {
                "relevance": 0.8,
                "clarity": 0.9,
                "fluency": 0.85,
            },
            "dimensions": ["relevance", "clarity", "fluency"],
        }
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "intro rubric" in prompt
    assert "candidate_profile" in prompt or "Software Engineer Intern" in prompt


def test_build_feedback_prompt_returns_string():
    prompt = EvaluationPromptBuilder.build_feedback_prompt(
        {
            "candidate_profile": CandidateProfile(
                most_recent_role="Software Engineer Intern",
                domain_keywords=["backend systems"],
            ),
            "experience_evidence": ExperienceEvidence(
                experience_name="Deterministic Email Attribution System",
                what="Designed a deterministic email attribution system",
            ),
            "phase_evaluations": [
                {"phase_name": "intro", "overall_score": 85}
            ],
            "communication_metrics": {
                "relevance": 0.8,
                "clarity": 0.9,
                "fluency": 0.85,
            },
            "interview_evaluation": {
                "overall_score": 89,
                "assessment_confidence": 0.92,
            },
        }
    )

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "Strong communication" not in prompt  # just to keep it generic