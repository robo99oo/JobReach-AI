from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app.api.routes.analytics import router as analytics_router
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.follow_ups import router as follow_ups_router
from app.api.routes.master_profile import router as master_profile_router
from app.api.routes.scheduler import router as scheduler_router
from app.core.config import settings
from app.workers.background_scheduler import (
    start_background_scheduler,
    stop_background_scheduler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start the background scheduler with FastAPI and stop it cleanly
    during application shutdown.
    """

    start_background_scheduler()

    try:
        yield
    finally:
        stop_background_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


app.include_router(master_profile_router)
app.include_router(campaigns_router)
app.include_router(follow_ups_router)
app.include_router(scheduler_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }