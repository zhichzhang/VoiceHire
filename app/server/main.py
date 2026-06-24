# app/server/main.py

from __future__ import annotations

from traceback import format_exc
from typing import Any, cast

from fastapi import FastAPI
from starlette.datastructures import State
from starlette.middleware.cors import CORSMiddleware

from app.server.apis import api_router
from app.server.core.config import settings
from app.server.core.logger import logger
from app.server.core.supabase_client import (
    get_supabase_client,
)

from app.server.interview.contracts.phase_types import (
    PhaseType,
)
from app.server.interview.engines.evaluation_engine import (
    EvaluationEngine,
)
from app.server.interview.engines.interview_engine import (
    InterviewEngine,
)
from app.server.interview.evaluators.turn_evaluators import TurnEvaluator
from app.server.interview.phases.experience_phase import (
    ExperiencePhase,
)
from app.server.interview.phases.intro_phase import (
    IntroPhase,
)

from app.server.llm.client import LLMClient
from app.server.llm.providers.gemini import (
    GeminiProvider,
)

from app.server.services.application_bootstrap_service import (
    ApplicationBootstrapService,
)
from app.server.services.interview_workflow_service import (
    InterviewWorkflowService,
)
from app.server.services.turn_scoring_service import (
    TurnScoringService,
)

app = FastAPI(
    title="VoiceHire API",
)

# ------------------------------------------------------------
# LLM wiring
# ------------------------------------------------------------
if not settings.gemini_api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set"
    )

llm_provider = GeminiProvider(
    api_key=settings.gemini_api_key,
    model_name=settings.gemini_model,
)

llm_client = LLMClient(
    provider=llm_provider,
)

# ------------------------------------------------------------
# Core interview engine wiring
# ------------------------------------------------------------
intro_turn_evaluator = TurnEvaluator(llm=llm_client)
experience_turn_evaluator = TurnEvaluator(llm=llm_client)

intro_phase = IntroPhase(
    llm=llm_client,
    turn_evaluator=intro_turn_evaluator,
)

experience_phase = ExperiencePhase(
    llm=llm_client,
    turn_evaluator=experience_turn_evaluator,
)

evaluation_engine = EvaluationEngine(
    llm=llm_client,
)

interview_engine = InterviewEngine(
    intro_phase=intro_phase,
    experience_phase=experience_phase,
    evaluation_engine=evaluation_engine,
)

# ------------------------------------------------------------
# Turn scoring wiring
# ------------------------------------------------------------
phases = {
    PhaseType.INTRO: intro_phase,
    PhaseType.EXPERIENCE: experience_phase,
}

turn_scoring_service = TurnScoringService(
    phases=phases,
)

# ------------------------------------------------------------
# Service wiring
# ------------------------------------------------------------
state: State = cast(Any, app).state

state.llm_client = llm_client

state.application_bootstrap_service = (
    ApplicationBootstrapService
)

state.turn_scoring_service = (
    turn_scoring_service
)

state.interview_workflow_service = (
    InterviewWorkflowService(
        engine=interview_engine,
        turn_scoring_service=turn_scoring_service,
    )
)

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
app.include_router(
    api_router,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Startup diagnostics
# ------------------------------------------------------------
logger.info(
    "===== VoiceHire Startup ====="
)

logger.info(
    f"APP_ENV={settings.app_env}"
)

logger.info(
    f"GEMINI_MODEL={settings.gemini_model}"
)

logger.success(
    "Gemini provider initialized"
)

logger.success(
    "Interview engine initialized"
)

logger.success(
    "Workflow service initialized"
)

# # ------------------------------------------------------------
# # Supabase warm-up
# # ------------------------------------------------------------
# try:
#     get_supabase_client()
#
#     logger.success(
#         "Supabase client warmed up"
#     )
#
# except Exception:
#     logger.warning(
#         "Supabase warm-up failed; continuing without startup abort"
#     )
#
#     logger.error(
#         format_exc()
#     )
#
# logger.success(
#     "FastAPI startup completed"
# )