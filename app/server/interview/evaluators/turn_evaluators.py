# app/server/interview/evaluators/turn_evaluators.py

from __future__ import annotations

from app.server.interview.contracts.phase_types import PhaseType
from app.server.llm.client import LLMClient
from app.server.llm.contracts.prompt_inputs import TurnAssessmentPromptInput
from app.server.models.assessment import TurnAssessment


class TurnEvaluator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def evaluate(
        self,
        phase: PhaseType,
        question: str,
        answer: str,
    ) -> TurnAssessment:
        result = await self.llm.evaluate_turn(
            TurnAssessmentPromptInput(
                phase=phase,
                question=question,
                answer=answer,
            )
        )

        return TurnAssessment(
            relevance=result.relevance,
            clarity=result.clarity,
            fluency=result.fluency,
        )