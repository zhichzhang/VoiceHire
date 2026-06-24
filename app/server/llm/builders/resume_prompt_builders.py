# app/server/llm/builders/resume_prompt_builders.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.server.llm.contracts.prompt_inputs import (
    ResumeNormalizationPromptInput,
)


class ResumePromptBuilder:
    """
    Build prompts for resume ingestion and normalization.

    This builder only renders prompt text.
    It does not call the LLM and does not persist state.
    """

    _PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
    _NORMALIZATION_TEMPLATE = _PROMPT_DIR / "resume" / "resume_normalization.txt"

    @staticmethod
    def build_normalization_prompt(
        input_data: ResumeNormalizationPromptInput,
    ) -> str:
        """
        Render the resume normalization prompt.

        Expected placeholders:
            - name
            - email
            - current_resume_context
            - raw_resume_text
        """
        template = ResumePromptBuilder._read_template(
            ResumePromptBuilder._NORMALIZATION_TEMPLATE
        )

        variables = {
            "name": input_data.name,
            "email": input_data.email,
            "current_resume_context": ResumePromptBuilder._stringify(
                input_data.current_resume_context
            ),
            "raw_resume_text": input_data.raw_resume_text,
        }

        return ResumePromptBuilder._render_template(template, variables)

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