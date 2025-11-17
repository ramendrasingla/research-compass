"""Pydantic models for API requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ResearchRequest(BaseModel):
    """Request model for starting a research session."""

    query: str
    search_api: str = "all"  # Default to searching all APIs for comprehensive coverage
    research_model: str = "openai:gpt-4o-mini"  # Using mini to avoid rate limits & save tokens
    summarization_model: str = "openai:gpt-4o-mini"
    max_researcher_iterations: int = 2  # Minimum: 1 for planning + 1 for research (reduced to save tokens)
    max_concurrent_research_units: int = 2  # Fewer parallel researchers to save tokens
    export_formats: List[str] = []
    allow_clarification: bool = True


class PaperSource(BaseModel):
    """Metadata for a research paper source."""

    source_id: str
    paper_id: Optional[str] = None
    title: str
    authors: List[str] = []
    abstract: str = ""
    url: str
    pdf_url: Optional[str] = None
    published_date: Optional[str] = None
    citation_count: Optional[int] = None
    venue: Optional[str] = None
    search_api: str
    accessed_at: str


class SessionInfo(BaseModel):
    """Information about a research session."""

    session_id: str
    query: str
    status: str
    created_at: str
    updated_at: str
    config: Dict[str, Any]


class ResearchResult(BaseModel):
    """Research session result data."""

    final_report: str
    exported_files: List[str] = []
    sources: List[PaperSource] = []


class SessionDetail(BaseModel):
    """Detailed information about a research session including results."""

    session_id: str
    query: str
    status: str
    created_at: str
    updated_at: str
    config: Dict[str, Any]
    result: ResearchResult | None = None


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
