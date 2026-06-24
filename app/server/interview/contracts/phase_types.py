# app/server/interview/phase_types.py

from enum import StrEnum


class PhaseType(StrEnum):

    INTRO = "intro"

    EXPERIENCE = "experience"

    EVALUATION = "evaluation"

    COMPLETED = "completed"

    UNKNOWN = "unknown"