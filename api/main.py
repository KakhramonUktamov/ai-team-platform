"""
FastAPI application entry point.
Run with: uvicorn api.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.agents import router as agents_router
from api.routes.chat import router as chat_router
from config import settings
from db.models import Base
from db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (dev-friendly).
    In production, use Alembic migrations instead."""
    if settings.environment == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="AI Team Platform",
    description="AI-Powered Workforce Platform API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "AI Team Platform",
        "version": "0.2.0",
        "status": "running",
        "provider": settings.llm_provider,
        "model": settings.active_model,
        "auth_mode": "clerk" if settings.clerk_secret_key else "dev",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
