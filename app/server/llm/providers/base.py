# app/server/llm/providers/base.py

from abc import ABC, abstractmethod
from typing import TypeVar

from app.server.llm.contracts.prompt_outputs import (
    LLMResponse,
)

T = TypeVar("T")


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        response_model: type[T] | None = None,
    ) -> LLMResponse[T]:
        """
        Generate a response from the underlying model.

        Implementations are responsible for:

        - Calling the provider API
        - Parsing structured output
        - Collecting token usage
        - Returning a standardized LLMResponse
        """
        pass