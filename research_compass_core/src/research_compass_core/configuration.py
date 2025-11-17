"""Configuration management for the Research Compass Core system."""

import os
from enum import Enum
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


class SearchAPI(Enum):
    """Enumeration of available research paper search API providers.

    Only academic/research sources are supported to ensure high-quality citations.
    """

    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    ALL = "all"  # Use all available research APIs (ArXiv + Semantic Scholar) - Default


class ExportFormat(Enum):
    """Enumeration of available export formats for research reports."""

    MARKDOWN = "md"
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    JSON = "json"
    TXT = "txt"


class Configuration(BaseModel):
    """Main configuration class for the Research Compass Core agent."""

    # General Configuration
    max_structured_output_retries: int = Field(
        default=3,
        metadata={
            "description": "Maximum number of retries for structured output calls from models"
        }
    )
    allow_clarification: bool = Field(
        default=True,
        metadata={
            "description": "Whether to allow the researcher to ask the user clarifying questions before starting research"
        }
    )
    max_concurrent_research_units: int = Field(
        default=5,
        metadata={
            "description": "Maximum number of research units to run concurrently. This will allow the researcher to use multiple sub-agents to conduct research. Note: with more concurrency, you may run into rate limits."
        }
    )

    # Research Configuration
    search_api: SearchAPI = Field(
        default=SearchAPI.ARXIV,
        metadata={
            "description": "Search API to use for research. Options: arxiv (academic papers only), semantic_scholar (200M+ papers, all disciplines), all (both ArXiv and Semantic Scholar - recommended)"
        }
    )
    max_researcher_iterations: int = Field(
        default=6,
        metadata={
            "description": "Maximum number of research iterations for the Research Supervisor. This is the number of times the Research Supervisor will reflect on the research and ask follow-up questions."
        }
    )
    max_react_tool_calls: int = Field(
        default=10,
        metadata={
            "description": "Maximum number of tool calling iterations to make in a single researcher step."
        }
    )

    # Model Configuration
    summarization_model: str = Field(
        default="openai:gpt-4.1-mini",
        metadata={
            "description": "Model for summarizing research results"
        }
    )
    summarization_model_max_tokens: int = Field(
        default=8192,
        metadata={
            "description": "Maximum output tokens for summarization model"
        }
    )
    max_content_length: int = Field(
        default=50000,
        metadata={
            "description": "Maximum character length for webpage content before summarization"
        }
    )
    research_model: str = Field(
        default="openai:gpt-4o-mini",
        metadata={
            "description": "Model for conducting research. Using gpt-4o-mini to avoid rate limits and save tokens."
        }
    )
    research_model_max_tokens: int = Field(
        default=10000,
        metadata={
            "description": "Maximum output tokens for research model"
        }
    )
    compression_model: str = Field(
        default="openai:gpt-4.1",
        metadata={
            "description": "Model for compressing research findings from sub-agents."
        }
    )
    compression_model_max_tokens: int = Field(
        default=8192,
        metadata={
            "description": "Maximum output tokens for compression model"
        }
    )
    final_report_model: str = Field(
        default="openai:gpt-4.1",
        metadata={
            "description": "Model for writing the final report from all research findings"
        }
    )
    final_report_model_max_tokens: int = Field(
        default=10000,
        metadata={
            "description": "Maximum output tokens for final report model"
        }
    )

    # Export Configuration
    export_formats: list[ExportFormat] = Field(
        default_factory=list,
        metadata={
            "description": "List of export formats for the research report. Empty list means no file export."
        }
    )
    export_directory: str = Field(
        default="./research_reports",
        metadata={
            "description": "Directory where exported reports are saved"
        }
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config.get("configurable", {}) if config else {}
        field_names = list(cls.model_fields.keys())
        values: dict[str, Any] = {
            field_name: os.environ.get(field_name.upper(), configurable.get(field_name))
            for field_name in field_names
        }
        return cls(**{k: v for k, v in values.items() if v is not None})

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
