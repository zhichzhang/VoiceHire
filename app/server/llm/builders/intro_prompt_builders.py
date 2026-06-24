# app/server/llm/builders/intro_prompt_builder.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.server.llm.contracts.prompt_inputs import (
    IntroExtractionPromptInput,
    IntroQuestionPromptInput,
)


class IntroPromptBuilder:
    """
    Build prompts for the intro phase.

    This builder is responsible only for rendering prompt
    text. It does not call the LLM and does not mutate any
    session state.
    """

    _PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
    _QUESTION_TEMPLATE = _PROMPT_DIR / "questions" / "intro_question_generation.txt"
    _EXTRACTION_TEMPLATE = _PROMPT_DIR / "extraction" / "intro_extraction.txt"

    @staticmethod
    def build_question_prompt(input_data: IntroQuestionPromptInput) -> str:
        """
        Render the intro question-generation prompt.

        Expected template placeholders:
            - candidate_profile
            - coverage
            - coverage_score
            - covered_fields
            - missing_fields
            - previous_questions
            - previous_answers
        """
        template = IntroPromptBuilder._read_template(
            IntroPromptBuilder._QUESTION_TEMPLATE
        )

        variables = {
            "candidate_profile": IntroPromptBuilder._stringify(
                input_data.candidate_profile
            ),
            "coverage": IntroPromptBuilder._stringify(input_data.coverage),
            "coverage_score": IntroPromptBuilder._stringify(
                input_data.coverage.score
            ),
            "covered_fields": IntroPromptBuilder._stringify(
                input_data.coverage.covered_fields
            ),
            "missing_fields": IntroPromptBuilder._stringify(
                input_data.coverage.missing_fields
            ),
            "previous_questions": IntroPromptBuilder._stringify(
                input_data.previous_questions
            ),
            "previous_answers": IntroPromptBuilder._stringify(
                input_data.previous_answers
            ),
        }

        return IntroPromptBuilder._render_template(template, variables)

    @staticmethod
    def build_extraction_prompt(
        input_data: IntroExtractionPromptInput,
    ) -> str:
        """
        Render the intro extraction prompt.

        Expected template placeholders:
            - answer
            - resume_context
            - current_profile

        The template may ignore some fields; that is fine.
        """
        template = IntroPromptBuilder._read_template(
            IntroPromptBuilder._EXTRACTION_TEMPLATE
        )

        variables = {
            "answer": input_data.answer,
            "resume_context": IntroPromptBuilder._stringify(
                input_data.resume_context
            ),
            "current_profile": IntroPromptBuilder._stringify(
                input_data.current_profile
            ),
        }

        return IntroPromptBuilder._render_template(template, variables)

    @staticmethod
    def _read_template(path: Path) -> str:
        """
        Read a prompt template from disk.

        Raises:
            FileNotFoundError: if the template file does not exist.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {path}"
            )

        return path.read_text(encoding="utf-8")

    @staticmethod
    def _render_template(template: str, variables: dict[str, str]) -> str:
        """
        Replace simple `{placeholder}` tokens without relying on
        str.format().

        This avoids accidental formatting failures caused by JSON
        examples inside prompt text files.
        """
        rendered = template

        for key, value in variables.items():
            rendered = rendered.replace(f"{{{key}}}", value)

        return rendered

    @staticmethod
    def _stringify(value: Any) -> str:
        """
        Convert Python / Pydantic values into prompt-friendly text.

        - Pydantic models are converted via model_dump()
        - dict/list/tuple values are rendered as pretty JSON
        - None becomes 'null'
        - scalars become plain strings
        """
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