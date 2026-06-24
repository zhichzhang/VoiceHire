# app/server/interview/phases/base_phase.py

from abc import ABC, abstractmethod

from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.coverage.coverage import (
    CoverageResult,
)
from app.server.interview.evaluators.turn_evaluators import TurnEvaluator
from app.server.llm.contracts.prompt_outputs import QuestionGenerationResult
from app.server.models.assessment import TurnAssessment

from app.server.models.session import (
    InterviewSession,
)


class InterviewPhase(ABC):
    """
    Base contract for all interview phases.

    A phase is responsible for:

    - Generating questions
    - Extracting structured information
    - Updating session state
    - Evaluating coverage
    - Determining completion
    """

    phase_name: PhaseType
    max_turns: int
    coverage_threshold: float
    turn_evaluator: TurnEvaluator | None = None

    @abstractmethod
    async def generate_question(
        self,
        session: InterviewSession,
    ) -> QuestionGenerationResult:
        """
        Generate the next question for the candidate.
        """
        pass

    @abstractmethod
    async def process_answer(
        self,
        session: InterviewSession,
        answer: str,
    ) -> None:
        """
        Process a candidate answer and update session state.

        This typically includes:

        - Information extraction
        - Profile/evidence updates
        - Turn assessment creation
        """
        pass

    @abstractmethod
    async def evaluate_coverage(
        self,
        session: InterviewSession,
    ) -> CoverageResult:
        """
        Evaluate current information coverage.
        """
        pass

    @staticmethod
    def _next_turn_number(
            session: InterviewSession,
    ) -> int:
        return len(session.turns) + 1

    async def is_complete(
        self,
        session: InterviewSession,
    ) -> bool:
        """
        Determine whether the phase should end.
        """

        coverage = await self.evaluate_coverage(
            session
        )

        if coverage.complete:
            return True

        phase_turns = [
            turn
            for turn in session.turns
            if turn.phase == self.phase_name
        ]

        return len(phase_turns) >= self.max_turns

    async def assess_turn(
        self,
        session: InterviewSession,
        question: str,
        answer: str,
    ) -> TurnAssessment:
        if self.turn_evaluator is None:
            return TurnAssessment(
                relevance=0.0,
                clarity=0.0,
                fluency=0.0,
            )

        return await self.turn_evaluator.evaluate(
            phase=self.phase_name,
            question=question,
            answer=answer,
        )