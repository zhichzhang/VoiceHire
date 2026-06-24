# app/server/interview/rubrics.py

from enum import StrEnum


class EvaluationDimension(StrEnum):

    RELEVANCE = "relevance"

    CLARITY = "clarity"

    FLUENCY = "fluency"

    OWNERSHIP = "ownership"

    PROBLEM_SOLVING = "problem_solving"

    IMPACT = "impact"

    DOMAIN_EXPERTISE = "domain_expertise"

ALL_DIMENSIONS = [
    EvaluationDimension.RELEVANCE,
    EvaluationDimension.CLARITY,
    EvaluationDimension.FLUENCY,
    EvaluationDimension.OWNERSHIP,
    EvaluationDimension.PROBLEM_SOLVING,
    EvaluationDimension.IMPACT,
    EvaluationDimension.DOMAIN_EXPERTISE,
]

INTRO_WEIGHTS = {

    EvaluationDimension.RELEVANCE: 0.25,

    EvaluationDimension.CLARITY: 0.35,

    EvaluationDimension.FLUENCY: 0.25,

    EvaluationDimension.OWNERSHIP: 0.00,

    EvaluationDimension.PROBLEM_SOLVING: 0.00,

    EvaluationDimension.IMPACT: 0.00,

    EvaluationDimension.DOMAIN_EXPERTISE: 0.15,
}

EXPERIENCE_WEIGHTS = {

    EvaluationDimension.RELEVANCE: 0.10,

    EvaluationDimension.CLARITY: 0.10,

    EvaluationDimension.FLUENCY: 0.05,

    EvaluationDimension.OWNERSHIP: 0.20,

    EvaluationDimension.PROBLEM_SOLVING: 0.25,

    EvaluationDimension.IMPACT: 0.15,

    EvaluationDimension.DOMAIN_EXPERTISE: 0.15,
}

INTERVIEW_WEIGHTS = {

    "intro": 0.25,

    "experience": 0.75,
}