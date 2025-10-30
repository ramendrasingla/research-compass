"""Pydantic models for API requests and responses."""

from typing import Any, Dict, List

from pydantic import BaseModel


class ResearchRequest(BaseModel):
    """Request model for starting a research session."""

    query: str
    search_api: str = "arxiv"
    research_model: str = "openai:gpt-4o"
    summarization_model: str = "openai:gpt-4o-mini"
    max_researcher_iterations: int = 6
    max_concurrent_research_units: int = 5
    export_formats: List[str] = []
    allow_clarification: bool = True


class SessionInfo(BaseModel):
    """Information about a research session."""

    session_id: str
    query: str
    status: str
    created_at: str
    updated_at: str
    config: Dict[str, Any]


class SessionDetail(BaseModel):
    """Detailed information about a research session including results."""

    session_id: str
    query: str
    status: str
    created_at: str
    updated_at: str
    config: Dict[str, Any]
    result: Dict[str, Any] | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    core_available: bool
    timestamp: str


class ModelListResponse(BaseModel):
    """List of available models."""

    models: List[str]


class SearchAPIInfo(BaseModel):
    """Information about a search API."""

    id: str
    name: str
    description: str


class SearchAPIListResponse(BaseModel):
    """List of available search APIs."""

    search_apis: List[SearchAPIInfo]


class ExportFormatInfo(BaseModel):
    """Information about an export format."""

    id: str
    name: str
    extension: str


class ExportFormatListResponse(BaseModel):
    """List of available export formats."""

    formats: List[ExportFormatInfo]


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
