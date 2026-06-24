# app/server/llm/builders/turn_assessment_prompt_builder.py

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.server.llm.contracts.prompt_inputs import TurnAssessmentPromptInput


class TurnAssessmentPromptBuilder:
    _PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
    _TEMPLATE = _PROMPT_DIR / "turn" / "turn_assessment.txt"

    @staticmethod
    def build_prompt(input_data: TurnAssessmentPromptInput) -> str:
        template = TurnAssessmentPromptBuilder._read_template(
            TurnAssessmentPromptBuilder._TEMPLATE
        )

        variables = {
            "phase": getattr(input_data.phase, "value", input_data.phase),
            "question": input_data.question,
            "answer": input_data.answer,
        }

        return TurnAssessmentPromptBuilder._render_template(template, variables)

    @staticmethod
    def _read_template(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _render_template(template: str, variables: dict[str, str]) -> str:
        rendered = template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        return rendered