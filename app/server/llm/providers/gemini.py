from __future__ import annotations

from typing import TypeVar

from google import genai

from app.server.llm.contracts.prompt_outputs import (
    LLMResponse,
    TokenUsage,
)
from app.server.llm.providers.base import LLMProvider
from app.server.services.structured_output_service import StructuredOutputService

T = TypeVar("T")


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
    ):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.structured_output = StructuredOutputService()

    async def generate(
        self,
        prompt: str,
        response_model: type[T] | None = None,
    ) -> LLMResponse[T]:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        text = response.text or ""
        print("\n===== RAW RESPONSE =====")
        print(repr(text))
        print("===== END RESPONSE =====\n")

        usage = self._extract_token_usage(response)

        if response_model is None:
            return LLMResponse(
                result=text,  # type: ignore[arg-type]
                token_usage=usage,
            )

        result = self.structured_output.parse_and_validate(text, response_model)

        return LLMResponse(
            result=result,
            token_usage=usage,
        )

    def _extract_token_usage(self, response) -> TokenUsage | None:
        usage_metadata = getattr(response, "usage_metadata", None)
        if usage_metadata is None:
            return None

        return TokenUsage(
            prompt_tokens=getattr(usage_metadata, "prompt_token_count", 0) or 0,
            completion_tokens=getattr(usage_metadata, "candidates_token_count", 0) or 0,
            total_tokens=getattr(usage_metadata, "total_token_count", 0) or 0,
        )