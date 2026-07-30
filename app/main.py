from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.master_profile import router as master_profile_router
from app.core.config import settings
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


app.include_router(master_profile_router)
app.include_router(campaigns_router)


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