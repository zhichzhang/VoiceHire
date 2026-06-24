# app/server/llm/builders/experience_prompt_builder.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.server.llm.contracts.prompt_inputs import (
    ExperienceExtractionPromptInput,
    ExperienceQuestionPromptInput,
)


class ExperiencePromptBuilder:
    """
    Build prompts for the experience phase.

    This builder only renders prompt text.
    It does not call the LLM and does not manage workflow state.
    """

    _PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
    _QUESTION_TEMPLATE = _PROMPT_DIR / "questions" / "experience_question_generation.txt"
    _DEEP_DIVE_TEMPLATE = _PROMPT_DIR / "questions" / "experience_deep_dive_question_generation.txt"
    _EXTRACTION_TEMPLATE = _PROMPT_DIR / "extraction" / "experience_extraction.txt"

    @staticmethod
    def build_question_prompt(input_data: ExperienceQuestionPromptInput) -> str:
        """
        Render the experience question-generation prompt.

        Mode:
            - collection: collect missing evidence fields
            - deep_dive: generate competency-focused follow-up

        Expected collection-mode placeholders:
            - candidate_profile
            - experience_evidence
            - coverage
            - coverage_score
            - coverage_threshold
            - covered_fields
            - missing_fields
            - previous_questions
            - previous_answers

        Expected deep-dive placeholders:
            - candidate_profile
            - experience_evidence
            - dimensions
            - previous_questions
            - previous_answers
        """
        if input_data.mode == "collection":
            template = ExperiencePromptBuilder._read_template(
                ExperiencePromptBuilder._QUESTION_TEMPLATE
            )

            variables = {
                "candidate_profile": ExperiencePromptBuilder._stringify(
                    input_data.candidate_profile
                ),
                "experience_evidence": ExperiencePromptBuilder._stringify(
                    input_data.experience_evidence
                ),
                "coverage": ExperiencePromptBuilder._stringify(
                    input_data.coverage
                ),
                "coverage_score": (
                    "" if input_data.coverage is None
                    else ExperiencePromptBuilder._stringify(
                        input_data.coverage.score
                    )
                ),
                "coverage_threshold": (
                    "" if input_data.coverage is None
                    else "0.8"
                ),
                "covered_fields": (
                    "" if input_data.coverage is None
                    else ExperiencePromptBuilder._stringify(
                        input_data.coverage.covered_fields
                    )
                ),
                "missing_fields": (
                    "" if input_data.coverage is None
                    else ExperiencePromptBuilder._stringify(
                        input_data.coverage.missing_fields
                    )
                ),
                "previous_questions": ExperiencePromptBuilder._stringify(
                    input_data.previous_questions
                ),
                "previous_answers": ExperiencePromptBuilder._stringify(
                    input_data.previous_answers
                ),
            }

            return ExperiencePromptBuilder._render_template(template, variables)

        if input_data.mode == "deep_dive":
            template = ExperiencePromptBuilder._read_template(
                ExperiencePromptBuilder._DEEP_DIVE_TEMPLATE
            )

            variables = {
                "candidate_profile": ExperiencePromptBuilder._stringify(
                    input_data.candidate_profile
                ),
                "experience_evidence": ExperiencePromptBuilder._stringify(
                    input_data.experience_evidence
                ),
                "dimensions": ExperiencePromptBuilder._stringify(
                    input_data.dimensions or []
                ),
                "previous_questions": ExperiencePromptBuilder._stringify(
                    input_data.previous_questions
                ),
                "previous_answers": ExperiencePromptBuilder._stringify(
                    input_data.previous_answers
                ),
            }

            return ExperiencePromptBuilder._render_template(template, variables)

        raise ValueError(
            f"Unsupported experience prompt mode: {input_data.mode}"
        )

    @staticmethod
    def build_extraction_prompt(
        input_data: ExperienceExtractionPromptInput,
    ) -> str:
        """
        Render the experience extraction prompt.

        Expected template placeholders:
            - answer
            - candidate_profile
            - resume_context
            - experience_context
        """
        template = ExperiencePromptBuilder._read_template(
            ExperiencePromptBuilder._EXTRACTION_TEMPLATE
        )

        variables = {
            "answer": input_data.answer,
            "candidate_profile": ExperiencePromptBuilder._stringify(
                input_data.candidate_profile
            ),
            "resume_context": ExperiencePromptBuilder._stringify(
                input_data.resume_context
            ),
            "experience_context": (
                "null"
                if input_data.experience_context is None
                else input_data.experience_context
            ),
        }

        return ExperiencePromptBuilder._render_template(template, variables)

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