"""API routes for configuration options."""

from fastapi import APIRouter

from app.models.schemas import (
    ExportFormatInfo,
    ExportFormatListResponse,
    ModelListResponse,
    SearchAPIInfo,
    SearchAPIListResponse,
)

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/models", response_model=ModelListResponse)
async def get_available_models() -> ModelListResponse:
    """
    Get list of available OpenAI models.

    Returns:
        List of available models
    """
    return ModelListResponse(
        models=[
            "openai:gpt-4o",
            "openai:gpt-4o-mini",
            "openai:gpt-4-turbo",
            "openai:o1",
            "openai:o3-mini",
        ]
    )


@router.get("/search-apis", response_model=SearchAPIListResponse)
async def get_available_search_apis() -> SearchAPIListResponse:
    """
    Get list of available search APIs.

    Returns:
        List of available search APIs with descriptions
    """
    return SearchAPIListResponse(
        search_apis=[
            SearchAPIInfo(
                id="arxiv",
                name="ArXiv",
                description="Academic papers in CS, physics, mathematics",
            ),
            SearchAPIInfo(
                id="semantic_scholar",
                name="Semantic Scholar",
                description="200M+ papers across all disciplines",
            ),
            SearchAPIInfo(
                id="openai",
                name="OpenAI Web Search",
                description="General web search via OpenAI",
            ),
            SearchAPIInfo(
                id="none",
                name="None",
                description="No search (custom tools only)",
            ),
        ]
    )


@router.get("/export-formats", response_model=ExportFormatListResponse)
async def get_export_formats() -> ExportFormatListResponse:
    """
    Get list of available export formats.

    Returns:
        List of available export formats with extensions
    """
    return ExportFormatListResponse(
        formats=[
            ExportFormatInfo(id="markdown", name="Markdown", extension=".md"),
            ExportFormatInfo(id="pdf", name="PDF", extension=".pdf"),
            ExportFormatInfo(id="html", name="HTML", extension=".html"),
            ExportFormatInfo(id="docx", name="Word Document", extension=".docx"),
            ExportFormatInfo(id="json", name="JSON", extension=".json"),
            ExportFormatInfo(id="txt", name="Plain Text", extension=".txt"),
        ]
    )
