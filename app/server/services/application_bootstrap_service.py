# app/server/services/application_bootstrap_service.py

from __future__ import annotations

import json
import uuid

from app.server.core.logger import logger
from app.server.interview.sessions.session_initializer import (
    SessionInitializer,
)
from app.server.interview.repositories.candidate_repository import (
    CandidateRepository,
)
from app.server.interview.repositories.resume_repository import (
    ResumeRepository,
)
from app.server.services.resume_preflight_analysis_service import (
    ResumeUpsertDecision,
    ResumePreflightAnalysisService,
)
from app.server.llm.client import LLMClient
from app.server.llm.contracts.prompt_inputs import (
    ResumeNormalizationPromptInput,
)
from app.server.models.application_bootstrap import ApplicationBootstrapResult
from app.server.models.resume import CandidateResume


class ApplicationBootstrapService:
    """
    Orchestrates the onboarding flow before interview start.

    Input:
    - email
    - name
    - pasted resume text

    Behavior:
    - empty resume text -> use existing resume if present
    - non-empty resume text -> preflight first, then normalize with LLM
    """

    @staticmethod
    async def bootstrap(
        email: str,
        name: str,
        raw_resume_text: str,
        llm: LLMClient,
    ) -> ApplicationBootstrapResult:
        logger.info(
            f"[BOOTSTRAP] start email={email} name={name} "
            f"raw_resume_len={len(raw_resume_text or '')}"
        )

        raw_resume_text = raw_resume_text.strip()
        logger.info(
            f"[BOOTSTRAP] after strip email={email} "
            f"raw_resume_len={len(raw_resume_text)}"
        )

        logger.info(f"[BOOTSTRAP] lookup candidate by email={email}")
        existing_candidate = CandidateRepository.get_by_email(email)
        is_new_candidate = existing_candidate is None
        logger.info(
            f"[BOOTSTRAP] candidate lookup done email={email} "
            f"is_new_candidate={is_new_candidate}"
        )

        existing_resume_row = None
        existing_resume_context = None

        if existing_candidate is not None:
            candidate_id = existing_candidate["id"]
            logger.info(
                f"[BOOTSTRAP] existing candidate found email={email} "
                f"candidate_id={candidate_id}"
            )
            existing_resume_row = ResumeRepository.get_by_candidate_id(
                candidate_id
            )
            logger.info(
                f"[BOOTSTRAP] resume lookup done email={email} "
                f"has_existing_resume={existing_resume_row is not None}"
            )

            if existing_resume_row is not None:
                resume_payload = existing_resume_row["resume_json"]

                if isinstance(resume_payload, str):
                    resume_payload = json.loads(resume_payload)

                existing_resume_context = (
                    SessionInitializer._build_resume_context(
                        resume_payload
                    )
                )
        else:
            candidate_id = str(uuid.uuid4())
            logger.info(
                f"[BOOTSTRAP] new candidate created email={email} "
                f"candidate_id={candidate_id}"
            )

        # ------------------------------------------------------------
        # Case 1: resume text is empty
        # ------------------------------------------------------------
        if not raw_resume_text:
            logger.info(
                f"[BOOTSTRAP] empty resume branch email={email} "
                f"has_existing_resume={existing_resume_row is not None}"
            )

            if existing_resume_row is None or existing_resume_context is None:
                logger.warning(
                    f"[BOOTSTRAP] empty resume rejected email={email} "
                    f"reason=no existing resume"
                )
                raise ValueError(
                    "Resume text is empty and no existing resume exists "
                    f"for email: {email}"
                )

            logger.info(
                f"[BOOTSTRAP] upserting candidate email={email} "
                f"candidate_id={candidate_id}"
            )
            candidate_row = CandidateRepository.upsert(
                candidate_id=candidate_id,
                email=email,
                name=name,
            )
            logger.info(
                f"[BOOTSTRAP] candidate upsert done email={email} "
                f"candidate_id={candidate_id}"
            )

            resume_row = existing_resume_row
            normalized_resume = existing_resume_context
            resume_updated = False
            used_existing_resume = True

            logger.info(
                f"[BOOTSTRAP] using existing resume email={email} "
                f"resume_updated={resume_updated} "
                f"used_existing_resume={used_existing_resume}"
            )

        # ------------------------------------------------------------
        # Case 2: resume text is present
        # ------------------------------------------------------------
        else:
            logger.info(
                f"[BOOTSTRAP] preflight start email={email} "
                f"raw_resume_len={len(raw_resume_text)}"
            )
            preflight = ResumePreflightAnalysisService.analyze(
                raw_resume_text=raw_resume_text,
                expected_email=email,
            )
            logger.info(
                f"[BOOTSTRAP] preflight done email={email} "
                f"decision={preflight.decision} "
                f"score={preflight.section_score} "
                f"matched_sections={preflight.matched_sections} "
                f"reasons={preflight.reasons}"
            )

            if preflight.decision == ResumeUpsertDecision.REJECT_MISMATCH:
                logger.info(
                    f"[BOOTSTRAP] reject mismatch branch email={email} "
                    f"has_existing_resume={existing_resume_row is not None}"
                )

                if existing_resume_row is None or existing_resume_context is None:
                    logger.warning(
                        f"[BOOTSTRAP] reject mismatch aborted email={email} "
                        f"reason=no existing resume"
                    )
                    raise ValueError(
                        "Resume text was rejected by preflight and no "
                        f"existing resume exists for email: {email}"
                    )

                candidate_row = existing_candidate
                resume_row = existing_resume_row
                normalized_resume = existing_resume_context
                resume_updated = False
                used_existing_resume = True

                logger.info(
                    f"[BOOTSTRAP] fallback to existing resume email={email}"
                )

            elif preflight.decision == ResumeUpsertDecision.USE_EXISTING:
                logger.info(
                    f"[BOOTSTRAP] use existing branch email={email} "
                    f"has_existing_resume={existing_resume_row is not None}"
                )

                if existing_resume_row is None or existing_resume_context is None:
                    logger.warning(
                        f"[BOOTSTRAP] use existing aborted email={email} "
                        f"reason=no existing resume"
                    )
                    raise ValueError(
                        "Resume text is empty and no existing resume exists "
                        f"for email: {email}"
                    )

                candidate_row = existing_candidate
                resume_row = existing_resume_row
                normalized_resume = existing_resume_context
                resume_updated = False
                used_existing_resume = True

                logger.info(
                    f"[BOOTSTRAP] using existing resume email={email}"
                )

            else:
                logger.info(
                    f"[BOOTSTRAP] normalize start email={email} "
                    f"has_existing_resume={existing_resume_row is not None}"
                )

                normalization_input = ResumeNormalizationPromptInput(
                    raw_resume_text=raw_resume_text,
                    name=name,
                    email=email,
                    current_resume_context=existing_resume_context,
                )

                logger.info(
                    f"[BOOTSTRAP] calling llm.normalize_resume email={email}"
                )
                normalized_resume = await llm.normalize_resume(
                    normalization_input
                )
                logger.info(
                    f"[BOOTSTRAP] llm.normalize_resume done email={email}"
                )

                logger.info(
                    f"[BOOTSTRAP] upserting candidate email={email} "
                    f"candidate_id={candidate_id}"
                )
                candidate_row = CandidateRepository.upsert(
                    candidate_id=candidate_id,
                    email=email,
                    name=name,
                )
                logger.info(
                    f"[BOOTSTRAP] candidate upsert done email={email} "
                    f"candidate_id={candidate_id}"
                )

                logger.info(
                    f"[BOOTSTRAP] upserting resume email={email} "
                    f"candidate_id={candidate_id}"
                )
                resume_row = ResumeRepository.upsert(
                    candidate_id=candidate_id,
                    resume_json=normalized_resume.model_dump(),
                )
                logger.info(
                    f"[BOOTSTRAP] resume upsert done email={email} "
                    f"candidate_id={candidate_id}"
                )

                resume_updated = True
                used_existing_resume = False

        logger.info(f"[BOOTSTRAP] session initialization start email={email}")
        session_bootstrap = SessionInitializer.initialize(
            email=email,
        )
        logger.info(
            f"[BOOTSTRAP] session initialization done email={email} "
            f"session_id={session_bootstrap.session.session_id}"
        )

        result = ApplicationBootstrapResult(
            candidate=candidate_row,
            resume=resume_row,
            session=session_bootstrap.session,
            normalized_resume=normalized_resume,
            is_new_candidate=is_new_candidate,
            resume_updated=resume_updated,
            used_existing_resume=used_existing_resume,
        )

        logger.info(
            f"[BOOTSTRAP] complete email={email} "
            f"session_id={result.session.session_id} "
            f"is_new_candidate={result.is_new_candidate} "
            f"resume_updated={result.resume_updated} "
            f"used_existing_resume={result.used_existing_resume}"
        )

        return result