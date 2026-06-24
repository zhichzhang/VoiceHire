# app/server/services/turn_scoring_service.py

from __future__ import annotations

import asyncio
from typing import Mapping

from app.server.core.logger import logger
from app.server.interview.contracts.phase_types import PhaseType
from app.server.interview.phases.base_phase import InterviewPhase
from app.server.interview.repositories.turn_repository import TurnRepository
from app.server.interview.sessions.session_loader import SessionLoader


class TurnScoringService:
    def __init__(
        self,
        phases: Mapping[PhaseType, InterviewPhase],
    ) -> None:
        self._phases = phases

    def schedule_turn_assessment(
        self,
        session_id: str,
        phase: PhaseType,
        turn_number: int,
        question: str,
        answer: str,
    ) -> asyncio.Task[None]:
        return asyncio.create_task(
            self.score_and_persist_turn(
                session_id=session_id,
                phase=phase,
                turn_number=turn_number,
                question=question,
                answer=answer,
            )
        )

    async def score_and_persist_turn(
        self,
        session_id: str,
        phase: PhaseType,
        turn_number: int,
        question: str,
        answer: str,
    ) -> None:
        phase_impl = self._phases.get(phase)
        if phase_impl is None:
            TurnRepository.mark_assessment_failed(
                session_id=session_id,
                turn_number=turn_number,
                error=f"Unsupported phase: {phase}",
            )
            return

        session = SessionLoader.load(session_id).session

        TurnRepository.mark_assessment_processing(
            session_id=session_id,
            turn_number=turn_number,
        )

        try:
            assessment = await phase_impl.assess_turn(
                session=session,
                question=question,
                answer=answer,
            )

            TurnRepository.update_assessment(
                session_id=session_id,
                turn_number=turn_number,
                relevance=assessment.relevance,
                clarity=assessment.clarity,
                fluency=assessment.fluency,
            )
        except Exception as exc:
            logger.error(
                f"Turn scoring failed | session_id={session_id} "
                f"turn_number={turn_number} | error={exc}"
            )
            TurnRepository.mark_assessment_failed(
                session_id=session_id,
                turn_number=turn_number,
                error=str(exc),
            )