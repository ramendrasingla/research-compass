"""Main FastAPI application for Research Compass UI."""

import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import config, research, sessions
from app.core.config import settings
from app.models.schemas import HealthResponse
from app.services.research_service import research_service

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
)


@app.on_event("startup")
async def startup_event():
    """Check configuration on startup."""
    print("\n" + "=" * 60)
    print("🧭 Research Compass UI Backend")
    print("=" * 60)

    # Check OpenAI API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   Please edit .env file and add your OpenAI API key")
        print("   Research will fail without it!")
    else:
        print(f"✓ OpenAI API key loaded (ends with ...{settings.openai_api_key[-4:]})")

    # Check research core
    if research_service.is_available():
        print("✓ research_compass_core loaded successfully")
    else:
        print("⚠️  WARNING: research_compass_core not available!")

    print(f"✓ Export directory: {settings.export_directory}")
    print(f"✓ Server running on: http://{settings.host}:{settings.port}")
    print("=" * 60 + "\n")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research.router)
app.include_router(sessions.router)
app.include_router(config.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Research Compass UI API",
        "version": settings.api_version,
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Health status with core availability
    """
    return HealthResponse(
        status="healthy",
        core_available=research_service.is_available(),
        timestamp=datetime.now().isoformat(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
