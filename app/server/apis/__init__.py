# app/server/apis/__init__.py

from fastapi import APIRouter

from app.server.apis.interview_routes import (
    router as interview_router,
)
from app.server.apis.transcribe_routes import (
    router as transcribe_router,
)

api_router = APIRouter()

api_router.include_router(interview_router)
api_router.include_router(transcribe_router)