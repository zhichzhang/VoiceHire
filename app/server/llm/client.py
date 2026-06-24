# app/server/llm/client.py

from __future__ import annotations

from typing import Any, TypeVar

from app.server.core.logger import logger
from app.server.llm.builders.evaluation_prompt_builders import EvaluationPromptBuilder
from app.server.llm.builders.experience_prompt_builders import ExperiencePromptBuilder
from app.server.llm.builders.intro_prompt_builders import IntroPromptBuilder
from app.server.llm.builders.resume_prompt_builders import ResumePromptBuilder
from app.server.llm.builders.turn_assessment_prompt_builder import TurnAssessmentPromptBuilder
from app.server.llm.contracts.prompt_inputs import (
    ExperienceExtractionPromptInput,
    ExperienceQuestionPromptInput,
    IntroExtractionPromptInput,
    IntroQuestionPromptInput, ResumeNormalizationPromptInput, TurnAssessmentPromptInput,
)
from app.server.llm.contracts.prompt_outputs import (
    ExperienceExtractionResult,
    InterviewFeedbackResult,
    IntroExtractionResult,
    LLMResponse,
    PhaseEvaluationResult,
    QuestionGenerationResult, TurnAssessmentResult,
)
from app.server.llm.providers.base import LLMProvider
from app.server.models.resume import CandidateResume

T = TypeVar("T")


class LLMClient:
    """
    High-level LLM facade.

    This class owns the end-to-end call path:
        typed input -> prompt builder -> rendered prompt -> provider -> typed output

    It keeps the application code clean by exposing semantic methods
    for each prompt family.
    """

    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider

    async def _invoke(
            self,
            operation: str,
            prompt: str,
            response_model: type[T] | None = None,
    ) -> T | str:
        """
        Low-level invocation helper.

        Most callers should use the semantic methods below.
        """

        logger.llm(
            f"START {operation} | "
            f"response_model="
            f"{response_model.__name__ if response_model else 'str'}"
        )

        logger.debug(
            f"PROMPT_LEN={len(prompt)}"
        )

        logger.debug(
            "PROMPT_PREVIEW=\n"
            + prompt[:2000]
        )

        try:
            call: LLMResponse[T] = await self.provider.generate(
                prompt=prompt,
                response_model=response_model,
            )

            if call.token_usage is not None:
                logger.llm(
                    f"{operation} | "
                    f"prompt={call.token_usage.prompt_tokens} | "
                    f"completion={call.token_usage.completion_tokens} | "
                    f"total={call.token_usage.total_tokens}"
                )

            logger.llm(
                f"SUCCESS {operation}"
            )

            logger.debug(
                f"RESULT_TYPE="
                f"{type(call.result).__name__}"
            )

            if hasattr(call.result, "model_dump_json"):
                logger.debug(
                    call.result.model_dump_json(
                        indent=2,
                        exclude_none=True,
                    )
                )

            logger.llm(
                f"END {operation}"
            )

            return call.result

        except Exception as exc:
            logger.error(
                f"FAILED {operation} | "
                f"{type(exc).__name__}: {exc}"
            )
            raise

    async def invoke(
        self,
        prompt: str,
        response_model: type[T] | None = None,
    ) -> T | str:
        """
        Public raw invocation interface.

        This is useful for tests or one-off calls that already have a rendered prompt.
        """
        logger.workflow(
            "[LLM_CLIENT] invoke"
        )

        return await self._invoke(
            operation="raw_invoke",
            prompt=prompt,
            response_model=response_model,
        )

    # =========================================================
    # Intro phase
    # =========================================================

    async def generate_intro_question(
        self,
        input_data: IntroQuestionPromptInput,
    ) -> QuestionGenerationResult:
        logger.workflow(
            "[LLM_CLIENT] generate_intro_question"
        )

        prompt = IntroPromptBuilder.build_question_prompt(input_data)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="intro_question_generation",
            prompt=prompt,
            response_model=QuestionGenerationResult,
        )

    async def extract_intro(
        self,
        input_data: IntroExtractionPromptInput,
    ) -> IntroExtractionResult:
        logger.workflow(
            "[LLM_CLIENT] extract_intro"
        )

        prompt = IntroPromptBuilder.build_extraction_prompt(input_data)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="intro_extraction",
            prompt=prompt,
            response_model=IntroExtractionResult,
        )

    # =========================================================
    # Experience phase
    # =========================================================

    async def generate_experience_question(
        self,
        input_data: ExperienceQuestionPromptInput,
    ) -> QuestionGenerationResult:
        logger.workflow(
            "[LLM_CLIENT] generate_experience_question"
        )

        prompt = ExperiencePromptBuilder.build_question_prompt(input_data)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="experience_question_generation",
            prompt=prompt,
            response_model=QuestionGenerationResult,
        )

    async def generate_experience_deep_dive_question(
        self,
        input_data: ExperienceQuestionPromptInput,
    ) -> QuestionGenerationResult:
        logger.workflow(
            "[LLM_CLIENT] generate_experience_deep_dive_question"
        )

        deep_dive_input = input_data.model_copy(update={"mode": "deep_dive"})
        prompt = ExperiencePromptBuilder.build_question_prompt(deep_dive_input)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="experience_deep_dive_question_generation",
            prompt=prompt,
            response_model=QuestionGenerationResult,
        )

    async def extract_experience(
        self,
        input_data: ExperienceExtractionPromptInput,
    ) -> ExperienceExtractionResult:
        logger.workflow(
            "[LLM_CLIENT] extract_experience"
        )

        prompt = ExperiencePromptBuilder.build_extraction_prompt(input_data)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="experience_extraction",
            prompt=prompt,
            response_model=ExperienceExtractionResult,
        )

    # =========================================================
    # Evaluation
    # =========================================================

    async def evaluate_phase(
        self,
        context: dict[str, Any],
    ) -> PhaseEvaluationResult:
        logger.workflow(
            "[LLM_CLIENT] evaluate_phase"
        )

        prompt = EvaluationPromptBuilder.build_evaluation_prompt(context)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="phase_evaluation",
            prompt=prompt,
            response_model=PhaseEvaluationResult,
        )

    async def generate_final_evaluation(
        self,
        context: dict[str, Any],
    ) -> InterviewFeedbackResult:
        logger.workflow(
            "[LLM_CLIENT] generate_final_evaluation"
        )

        prompt = EvaluationPromptBuilder.build_feedback_prompt(context)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="final_evaluation",
            prompt=prompt,
            response_model=InterviewFeedbackResult,
        )

    async def normalize_resume(
        self,
        input_data: ResumeNormalizationPromptInput,
    ) -> CandidateResume:
        logger.workflow(
            "[LLM_CLIENT] normalize_resume"
        )

        prompt = ResumePromptBuilder.build_normalization_prompt(input_data)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="resume_normalization",
            prompt=prompt,
            response_model=CandidateResume,
        )

    async def evaluate_turn(
            self,
            input_data: TurnAssessmentPromptInput,
    ) -> TurnAssessmentResult:
        logger.workflow(
            "[LLM_CLIENT] evaluate_turn"
        )

        prompt = TurnAssessmentPromptBuilder.build_prompt(input_data)

        logger.debug(
            f"[LLM_CLIENT] prompt_len={len(prompt)}"
        )

        return await self._invoke(
            operation="turn_assessment",
            prompt=prompt,
            response_model=TurnAssessmentResult,
        )