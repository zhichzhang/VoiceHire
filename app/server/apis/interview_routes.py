# app/server/apis/interview_routes.py

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.server.core.logger import logger
from app.server.services.application_bootstrap_service import (
    ApplicationBootstrapService,
)
from app.server.services.interview_workflow_service import (
    INTRO_FIXED_QUESTION,
    INTRO_FIXED_TIME_LIMIT_SECONDS,
    InterviewWorkflowService,
)

router = APIRouter(prefix="/interview", tags=["interview"])

SESSION_COOKIE_NAME = "voicehire_session_id"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

PhaseName = Literal["intro", "experience"]


class BootstrapRequest(BaseModel):
    email: str = Field(
        description="Candidate email used to start a fresh session."
    )
    name: str = Field(
        description="Candidate name used during onboarding."
    )
    raw_resume_text: str | None = Field(
        default=None,
        description="Optional pasted resume text."
    )


class ResumeRequest(BaseModel):
    session_id: str | None = Field(
        default=None,
        description="Session UUID entered by the user."
    )


class PhaseTranscriptRequest(BaseModel):
    text: str = Field(
        description="Final transcript text returned by LiveKit STT."
    )


def _get_workflow_service(request: Request) -> InterviewWorkflowService:
    service = getattr(request.app.state, "interview_workflow_service", None)
    if service is None:
        raise HTTPException(
            status_code=500,
            detail="InterviewWorkflowService is not configured.",
        )
    return service


def _get_bootstrap_service(request: Request) -> ApplicationBootstrapService:
    service = getattr(request.app.state, "application_bootstrap_service", None)
    if service is None:
        raise HTTPException(
            status_code=500,
            detail="ApplicationBootstrapService is not configured.",
        )
    return service


def _get_llm_client(request: Request):
    llm_client = getattr(request.app.state, "llm_client", None)
    if llm_client is None:
        raise HTTPException(
            status_code=500,
            detail="LLM client is not configured.",
        )
    return llm_client


@router.post("/bootstrap")
async def bootstrap(
    payload: BootstrapRequest,
    response: Response,
    request: Request,
):
    """
    Start a new application + interview session.

    This initializes the candidate profile / resume context,
    then seeds the fixed intro question.
    """
    print("[BOOTSTRAP ROUTE HIT]", payload.email, flush=True)
    logger.workflow(f"[INTERVIEW] BOOTSTRAP email={payload.email}")
    logger.debug(
        f"[INTERVIEW] BOOTSTRAP payload "
        f"email={payload.email!r} "
        f"name={payload.name!r} "
        f"raw_resume_len={len(payload.raw_resume_text or '')}"
    )

    bootstrap_service = _get_bootstrap_service(request)
    workflow_service = _get_workflow_service(request)
    llm_client = _get_llm_client(request)

    try:
        result = await bootstrap_service.bootstrap(
            email=payload.email,
            name=payload.name,
            raw_resume_text=payload.raw_resume_text or "",
            llm=llm_client,
        )
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception))

    logger.workflow(
        f"[INTERVIEW] BOOTSTRAP_DONE session={result.session.session_id}"
    )
    logger.debug(
        f"[INTERVIEW] BOOTSTRAP result "
        f"session_id={result.session.session_id} "
        f"candidate_id={(result.candidate or {}).get('id')} "
        f"resume_candidate_id={(result.resume or {}).get('candidate_id')}"
    )

    seeded = workflow_service.seed_intro_question(result.session)

    logger.workflow(
        f"[INTERVIEW] INTRO_SEEDED session={result.session.session_id}"
    )
    logger.debug(
        f"[INTERVIEW] INTRO_SEEDED result "
        f"kind={seeded.kind!r} "
        f"phase={seeded.phase!r} "
        f"text_len={len(seeded.text or '') if seeded.text else 0}"
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result.session.session_id,
        httponly=True,
        samesite="lax",
        max_age=SESSION_COOKIE_MAX_AGE,
    )

    logger.debug(
        f"[INTERVIEW] COOKIE_SET session={result.session.session_id}"
    )

    return {
        "candidate": result.candidate,
        "resume": result.resume,
        "normalized_resume": result.normalized_resume.model_dump(),
        "is_new_candidate": result.is_new_candidate,
        "resume_updated": result.resume_updated,
        "used_existing_resume": result.used_existing_resume,
        "session": (
            seeded.session.model_dump()
            if seeded.session is not None
            else result.session.model_dump()
        ),
        "first_question": {
            "text": INTRO_FIXED_QUESTION,
            "time_limit_seconds": INTRO_FIXED_TIME_LIMIT_SECONDS,
        },
    }


@router.post("/resume")
def resume(
    payload: ResumeRequest,
    request: Request,
    session_cookie: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE_NAME,
    ),
):
    """
    Resume an existing session by UUID or cookie.
    """
    logger.workflow(
        f"[INTERVIEW] RESUME_REQUEST session_id={payload.session_id} "
        f"cookie_present={session_cookie is not None}"
    )

    service = _get_workflow_service(request)

    session_id = payload.session_id or session_cookie
    if not session_id:
        logger.warning(
            "[INTERVIEW] RESUME_MISSING_SESSION_ID"
        )
        raise HTTPException(
            status_code=400,
            detail="session_id is required either in the request body or cookie.",
        )

    loaded = service.load_bundle(session_id)

    logger.success(
        f"[INTERVIEW] RESUME_LOADED session={session_id}"
    )

    return {
        "candidate": loaded.candidate,
        "resume": loaded.resume,
        "session": loaded.session.model_dump(),
    }


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    request: Request,
):
    """
    Load a session directly by UUID.
    """
    logger.workflow(
        f"[INTERVIEW] GET_SESSION session={session_id}"
    )

    service = _get_workflow_service(request)
    loaded = service.load_bundle(session_id)

    logger.debug(
        f"[INTERVIEW] SESSION_PHASE={loaded.session.current_phase}"
    )

    return {
        "candidate": loaded.candidate,
        "resume": loaded.resume,
        "session": loaded.session.model_dump(),
    }


@router.get("/sessions/{session_id}/report")
def get_report(
    session_id: str,
    request: Request,
):
    """
    Return the full report payload for rendering.
    """
    logger.workflow(
        f"[INTERVIEW] GET_REPORT session={session_id}"
    )

    service = _get_workflow_service(request)
    loaded = service.load_bundle(session_id)

    logger.debug(
        f"[INTERVIEW] REPORT_TURNS={len(loaded.session.turns)}"
    )

    return {
        "session": loaded.session.model_dump(),
        "evaluation": (
            loaded.session.evaluation.model_dump()
            if loaded.session.evaluation
            else None
        ),
        "turns": [turn.model_dump() for turn in loaded.session.turns],
    }


@router.post("/sessions/{session_id}/phases/{phase}/transcript")
async def submit_phase_transcript(
    session_id: str,
    phase: PhaseName,
    payload: PhaseTranscriptRequest,
    request: Request,
):
    """
    Submit one final transcript for the current phase.

    Frontend flow:
    - LiveKit returns final transcript text
    - frontend posts it here together with the current phase
    - workflow service decides whether to generate another question,
      advance to the next phase, or wait for explicit finalization
    """
    logger.workflow(
        f"[INTERVIEW] SUBMIT_TRANSCRIPT session={session_id} phase={phase}"
    )

    logger.debug(
        f"[INTERVIEW] TRANSCRIPT_LEN={len(payload.text)}"
    )

    service = _get_workflow_service(request)
    result = await service.submit_phase_transcript(
        session_id=session_id,
        phase=phase,
        text=payload.text,
    )

    logger.workflow(
        f"[INTERVIEW] SUBMIT_TRANSCRIPT_DONE session={session_id} "
        f"kind={result.kind} phase={result.phase}"
    )

    return result.model_dump()


@router.post("/sessions/{session_id}/evaluation")
async def finalize_session(
    session_id: str,
    request: Request,
):
    """
    Explicitly generate the final evaluation report.
    """
    logger.workflow(
        f"[INTERVIEW] FINALIZE_SESSION session={session_id}"
    )

    service = _get_workflow_service(request)
    result = await service.finalize(session_id)

    logger.success(
        f"[INTERVIEW] FINALIZE_SESSION_DONE session={session_id}"
    )

    return result.model_dump()


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    request: Request,
    response: Response,
):
    """
    Completely abandon an interview session.
    """
    logger.warning(
        f"[INTERVIEW] DELETE_SESSION session={session_id}"
    )

    service = _get_workflow_service(request)
    service.delete_session(session_id)

    response.delete_cookie(key=SESSION_COOKIE_NAME)

    logger.success(
        f"[INTERVIEW] DELETE_SESSION_DONE session={session_id}"
    )

    return {"deleted": True, "session_id": session_id}

@router.get("/health")
def interview_health(
    request: Request,
):
    workflow_service = getattr(
        request.app.state,
        "interview_workflow_service",
        None,
    )

    bootstrap_service = getattr(
        request.app.state,
        "application_bootstrap_service",
        None,
    )

    llm_client = getattr(
        request.app.state,
        "llm_client",
        None,
    )

    return {
        "ok": True,
        "service": "interview",
        "workflow_service": workflow_service is not None,
        "bootstrap_service": bootstrap_service is not None,
        "llm_client": llm_client is not None,
    }