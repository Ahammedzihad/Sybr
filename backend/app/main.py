"""
FastAPI application entrypoint for AI Security Analytics.
Configures middleware, routes, database lifecycle, and error handling.
"""

from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analyze, conversations, dashboard
from app.core.config import settings
from app.core.logging import logger
from app.database.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    # Initialize SQLite database schema
    init_db()
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered email and message security analysis platform using rule-based heuristics and Google Gemini AI.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    summary="Service health check",
    tags=["System"],
    response_model=Dict[str, str],
)
def health_check():
    """Returns application status and mode."""
    return {
        "status": "ok",
        "version": settings.VERSION,
        "mock_mode": str(settings.GEMINI_MOCK_MODE).lower(),
        "database": "connected",
    }


# Register core feature routers
app.include_router(analyze.router)
app.include_router(conversations.router)
app.include_router(dashboard.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler preventing sensitive stack traces from leaking."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
