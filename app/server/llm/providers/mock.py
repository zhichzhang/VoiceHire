# app/server/llm/providers/mock.py

from __future__ import annotations

import json
from typing import Any, TypeVar

from app.server.llm.contracts.prompt_outputs import (
    LLMResponse,
    TokenUsage,
)
from app.server.llm.providers.base import LLMProvider

T = TypeVar("T")


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock provider used for tests.

    This provider never calls a real LLM.
    It simply returns the predefined response so that
    LLMClient, prompt builders, and output schemas can be tested
    in isolation.

    The provider also records every call for assertions.
    """

    def __init__(
        self,
        response: dict[str, Any] | str,
        token_usage: TokenUsage | None = None,
    ):
        self.response = response
        self.token_usage = token_usage or TokenUsage()
        self.calls: list[dict[str, Any]] = []

    async def generate(
        self,
        prompt: str,
        response_model: type[T] | None = None,
    ) -> LLMResponse[T]:
        self.calls.append(
            {
                "prompt": prompt,
                "response_model": response_model,
            }
        )

        if response_model is None:
            if isinstance(self.response, str):
                result = self.response
            else:
                result = json.dumps(
                    self.response,
                    ensure_ascii=False,
                )
        else:
            result = response_model.model_validate(self.response)

        return LLMResponse(
            result=result,
            token_usage=self.token_usage,
        )