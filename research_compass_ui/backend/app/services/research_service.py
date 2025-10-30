"""Research service for executing research tasks using LangGraph."""

from typing import Any, AsyncGenerator, Dict, Optional

from langchain_core.messages import HumanMessage

# Import research_compass_core
try:
    from research_compass_core import graph
    from research_compass_core.configuration import Configuration, ExportFormat, SearchAPI

    CORE_AVAILABLE = True
except ImportError:
    print("Warning: research_compass_core not found. Install it first.")
    graph = None
    Configuration = None
    ExportFormat = None
    SearchAPI = None
    CORE_AVAILABLE = False


class ResearchService:
    """Service for managing research operations."""

    def __init__(self):
        """Initialize the research service."""
        self.core_available = CORE_AVAILABLE

    def is_available(self) -> bool:
        """
        Check if the research core is available.

        Returns:
            True if research_compass_core is available, False otherwise
        """
        return self.core_available

    def create_configuration(
        self,
        search_api: str,
        research_model: str,
        summarization_model: str,
        max_researcher_iterations: int,
        max_concurrent_research_units: int,
        export_formats: list[str],
        export_directory: str,
        allow_clarification: bool,
    ) -> Any:
        """
        Create a Configuration object for the research.

        Args:
            search_api: Search API to use
            research_model: Model for research
            summarization_model: Model for summarization
            max_researcher_iterations: Maximum iterations
            max_concurrent_research_units: Max concurrent units
            export_formats: List of export format strings
            export_directory: Directory to export reports
            allow_clarification: Whether to allow clarification

        Returns:
            Configuration object
        """
        if not self.core_available:
            raise RuntimeError("research_compass_core not available")

        # Parse export formats
        parsed_formats = []
        for fmt in export_formats:
            try:
                parsed_formats.append(ExportFormat[fmt.upper()])
            except KeyError:
                pass

        # Parse search API
        try:
            parsed_search_api = SearchAPI[search_api.upper()]
        except KeyError:
            parsed_search_api = SearchAPI.ARXIV

        return Configuration(
            search_api=parsed_search_api,
            research_model=research_model,
            summarization_model=summarization_model,
            max_researcher_iterations=max_researcher_iterations,
            max_concurrent_research_units=max_concurrent_research_units,
            export_formats=parsed_formats,
            export_directory=export_directory,
            allow_clarification=allow_clarification,
        )

    async def run_research(
        self,
        query: str,
        session_id: str,
        configuration: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the research graph and stream updates.

        Args:
            query: The research query
            session_id: Session ID for the research
            configuration: Configuration object

        Yields:
            Progress updates and final result
        """
        if not self.core_available:
            raise RuntimeError("research_compass_core not available")

        # Prepare graph config
        graph_config = {
            "configurable": {
                "thread_id": session_id,
                **configuration.model_dump(),
            }
        }

        # Stream the research process
        async for event in graph.astream(
            {"messages": [HumanMessage(content=query)]},
            graph_config,
            stream_mode="updates",
        ):
            yield event

    @staticmethod
    def extract_result(final_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract the final report and exported files from the graph state.

        Args:
            final_state: The final state from the graph

        Returns:
            Dictionary with final_report and exported_files, or None
        """
        final_report = None
        exported_files = []

        for node_name, node_data in final_state.items():
            if isinstance(node_data, dict):
                if "final_report" in node_data:
                    final_report = node_data["final_report"]
                if "exported_files" in node_data:
                    exported_files = node_data["exported_files"]

        if final_report is not None or exported_files:
            return {
                "final_report": final_report,
                "exported_files": exported_files,
            }
        return None


# Global research service instance
research_service = ResearchService()
