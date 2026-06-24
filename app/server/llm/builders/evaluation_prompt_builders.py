# app/server/llm/builders/evaluation_prompt_builder.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class EvaluationPromptBuilder:
    """
    Build prompts for evaluation and final reporting.

    This builder only renders prompt text.
    It does not score candidates and does not call the LLM.
    """

    _PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
    _EVALUATION_TEMPLATE = _PROMPT_DIR / "final" / "evaluation.txt"
    _FEEDBACK_TEMPLATE = _PROMPT_DIR / "final" / "llm_interview_feedback.txt"

    @staticmethod
    def build_evaluation_prompt(context: Mapping[str, Any]) -> str:
        """
        Render the phase-evaluation prompt.

        Expected context keys (recommended):
            - phase_name
            - rubric
            - candidate_profile
            - resume_context
            - experience_evidence
            - communication_metrics
            - dimensions
            - interview_transcript
        """
        template = EvaluationPromptBuilder._read_template(
            EvaluationPromptBuilder._EVALUATION_TEMPLATE
        )

        variables = {
            "phase_name": EvaluationPromptBuilder._stringify(
                context.get("phase_name")
            ),
            "rubric": EvaluationPromptBuilder._stringify(
                context.get("rubric")
            ),
            "candidate_profile": EvaluationPromptBuilder._stringify(
                context.get("candidate_profile")
            ),
            "resume_context": EvaluationPromptBuilder._stringify(
                context.get("resume_context")
            ),
            "experience_evidence": EvaluationPromptBuilder._stringify(
                context.get("experience_evidence")
            ),
            "communication_metrics": EvaluationPromptBuilder._stringify(
                context.get("communication_metrics")
            ),
            "dimensions": EvaluationPromptBuilder._stringify(
                context.get("dimensions", [])
            ),
            "interview_transcript": EvaluationPromptBuilder._stringify(
                context.get("interview_transcript", [])
            ),
        }

        return EvaluationPromptBuilder._render_template(template, variables)

    @staticmethod
    def build_feedback_prompt(context: Mapping[str, Any]) -> str:
        """
        Render the final interview feedback prompt.

        Expected context keys (recommended):
            - candidate_profile
            - resume_context
            - experience_evidence
            - phase_evaluations
            - communication_metrics
            - interview_transcript
            - interview_evaluation
        """
        template = EvaluationPromptBuilder._read_template(
            EvaluationPromptBuilder._FEEDBACK_TEMPLATE
        )

        variables = {
            "candidate_profile": EvaluationPromptBuilder._stringify(
                context.get("candidate_profile")
            ),
            "resume_context": EvaluationPromptBuilder._stringify(
                context.get("resume_context")
            ),
            "experience_evidence": EvaluationPromptBuilder._stringify(
                context.get("experience_evidence")
            ),
            "phase_evaluations": EvaluationPromptBuilder._stringify(
                context.get("phase_evaluations")
            ),
            "communication_metrics": EvaluationPromptBuilder._stringify(
                context.get("communication_metrics")
            ),
            "interview_transcript": EvaluationPromptBuilder._stringify(
                context.get("interview_transcript", [])
            ),
            "interview_evaluation": EvaluationPromptBuilder._stringify(
                context.get("interview_evaluation")
            ),
        }

        return EvaluationPromptBuilder._render_template(template, variables)

    @staticmethod
    def _read_template(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {path}"
            )

        return path.read_text(encoding="utf-8")

    @staticmethod
    def _render_template(template: str, variables: dict[str, str]) -> str:
        rendered = template

        for key, value in variables.items():
            rendered = rendered.replace(f"{{{key}}}", value)

        return rendered

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return "null"

        if hasattr(value, "model_dump"):
            value = value.model_dump()

        if isinstance(value, (dict, list, tuple)):
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        return str(value)