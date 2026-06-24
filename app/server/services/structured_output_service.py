from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class StructuredOutputParseError(ValueError):
    """
    Raised when an LLM response cannot be cleaned, parsed, or validated
    as structured JSON.
    """


@dataclass(frozen=True)
class StructuredOutputService:
    """
    Shared structured-output cleanup and parsing service.

    Responsibilities:
    - Strip markdown code fences
    - Extract the first balanced JSON object/array from noisy model output
    - Parse JSON
    - Validate against a Pydantic response model
    """

    max_preview_chars: int = 500

    def parse_json(self, text: str) -> Any:
        """
        Parse a raw LLM text response into a Python object.

        Supports:
        - raw JSON
        - fenced JSON blocks
        - JSON surrounded by extra explanatory text
        """
        cleaned = self._strip_code_fences(text)

        if not cleaned:
            raise StructuredOutputParseError(
                "LLM returned an empty response for structured output."
            )

        # First attempt: strict direct JSON parse.
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fallback: extract a balanced JSON fragment from noisy output.
        fragment = self._extract_first_json_fragment(cleaned)

        try:
            return json.loads(fragment)
        except json.JSONDecodeError as exc:
            preview = fragment[: self.max_preview_chars]
            raise StructuredOutputParseError(
                "LLM returned malformed structured output. "
                f"Could not parse JSON fragment: {preview!r}"
            ) from exc

    def parse_and_validate(
        self,
        text: str,
        response_model: type[TModel],
    ) -> TModel:
        """
        Parse raw text and validate it against the provided Pydantic model.
        """
        payload = self.parse_json(text)
        try:
            return response_model.model_validate(payload)
        except Exception as exc:
            preview = repr(payload)[: self.max_preview_chars]
            raise StructuredOutputParseError(
                "Structured output parsed as JSON but failed schema validation. "
                f"Payload preview: {preview}"
            ) from exc

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """
        Remove common markdown code fences surrounding JSON.
        """
        cleaned = text.strip()

        cleaned = re.sub(
            r"^```(?:json|JSON)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s*```$", "", cleaned)

        return cleaned.strip()

    @staticmethod
    def _extract_first_json_fragment(text: str) -> str:
        """
        Extract the first balanced JSON object or array from a string.

        This is more robust than naive substring slicing because it respects
        nested braces and quoted strings.
        """
        start_index: int | None = None
        opening_char: str | None = None

        for idx, ch in enumerate(text):
            if ch in "{[":
                start_index = idx
                opening_char = ch
                break

        if start_index is None or opening_char is None:
            raise StructuredOutputParseError(
                f"No JSON object or array found in LLM response: {text[:200]!r}"
            )

        stack: list[str] = [opening_char]
        in_string = False
        escape = False

        for idx in range(start_index + 1, len(text)):
            ch = text[idx]

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch in "{[":
                stack.append(ch)
                continue

            if ch in "}]":
                if not stack:
                    raise StructuredOutputParseError(
                        f"Unexpected closing delimiter in LLM response: {text[:200]!r}"
                    )

                last_open = stack.pop()
                expected_close = "}" if last_open == "{" else "]"

                if ch != expected_close:
                    raise StructuredOutputParseError(
                        f"Mismatched JSON delimiters in LLM response: {text[:200]!r}"
                    )

                if not stack:
                    return text[start_index : idx + 1]

        raise StructuredOutputParseError(
            f"Incomplete JSON fragment in LLM response: {text[:200]!r}"
        )