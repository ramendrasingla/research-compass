"""Unit tests for research tools (ArXiv and Semantic Scholar).

These tests verify tool structure and configuration without making actual API calls.
"""

from research_compass_core.arxiv_tools import get_arxiv_tools
from research_compass_core.semantic_scholar_tools import get_semantic_scholar_tools
from research_compass_core.configuration import SearchAPI, Configuration


class TestArxivTools:
    """Unit tests for ArXiv tools."""

    def test_get_arxiv_tools(self):
        """Test that get_arxiv_tools returns correct number of tools."""
        tools = get_arxiv_tools()
        assert len(tools) == 2, "Should return 2 tools (search and read_paper)"

    def test_arxiv_search_tool_structure(self):
        """Test ArXiv search tool has proper structure."""
        tools = get_arxiv_tools()
        search_tool = tools[0]

        assert search_tool.name == "arxiv_search"
        assert search_tool.description is not None
        assert "arXiv" in search_tool.description or "arxiv" in search_tool.description
        assert callable(search_tool.coroutine) or callable(search_tool.func)

    def test_arxiv_read_paper_tool_structure(self):
        """Test ArXiv read paper tool has proper structure."""
        tools = get_arxiv_tools()
        read_tool = tools[1]

        assert read_tool.name == "arxiv_read_paper"
        assert read_tool.description is not None
        assert "full text" in read_tool.description.lower() or "download" in read_tool.description.lower()
        assert callable(read_tool.coroutine) or callable(read_tool.func)


class TestSemanticScholarTools:
    """Unit tests for Semantic Scholar tools."""

    def test_get_semantic_scholar_tools(self):
        """Test that get_semantic_scholar_tools returns correct number of tools."""
        tools = get_semantic_scholar_tools()
        assert len(tools) == 2, "Should return 2 tools (search and get_paper)"

    def test_semantic_scholar_search_tool_structure(self):
        """Test Semantic Scholar search tool has proper structure."""
        tools = get_semantic_scholar_tools()
        search_tool = tools[0]

        assert search_tool.name == "semantic_scholar_search"
        assert search_tool.description is not None
        assert "200" in search_tool.description, "Should mention 200M+ papers"
        assert callable(search_tool.coroutine) or callable(search_tool.func)

    def test_semantic_scholar_get_paper_tool_structure(self):
        """Test Semantic Scholar get paper tool has proper structure."""
        tools = get_semantic_scholar_tools()
        get_paper_tool = tools[1]

        assert get_paper_tool.name == "semantic_scholar_get_paper"
        assert get_paper_tool.description is not None
        assert "paper id" in get_paper_tool.description.lower()
        assert callable(get_paper_tool.coroutine) or callable(get_paper_tool.func)


class TestConfiguration:
    """Unit tests for configuration."""

    def test_search_api_enum(self):
        """Test SearchAPI enum has all expected values."""
        assert hasattr(SearchAPI, "ARXIV")
        assert hasattr(SearchAPI, "SEMANTIC_SCHOLAR")
        assert hasattr(SearchAPI, "OPENAI")
        assert hasattr(SearchAPI, "NONE")

    def test_search_api_values(self):
        """Test SearchAPI enum values are correct."""
        assert SearchAPI.ARXIV.value == "arxiv"
        assert SearchAPI.SEMANTIC_SCHOLAR.value == "semantic_scholar"
        assert SearchAPI.OPENAI.value == "openai"
        assert SearchAPI.NONE.value == "none"

    def test_configuration_defaults(self):
        """Test Configuration has sensible defaults."""
        config = Configuration()

        # Check search API default
        assert config.search_api == SearchAPI.ARXIV

        # Check iteration limits
        assert config.max_researcher_iterations > 0
        assert config.max_react_tool_calls > 0
        assert config.max_concurrent_research_units > 0

        # Check models are set
        assert config.research_model is not None
        assert config.summarization_model is not None
        assert config.compression_model is not None
        assert config.final_report_model is not None

    def test_configuration_search_api_customization(self):
        """Test that search API can be customized."""
        # Test with ArXiv
        config_arxiv = Configuration(search_api=SearchAPI.ARXIV)
        assert config_arxiv.search_api == SearchAPI.ARXIV

        # Test with Semantic Scholar
        config_s2 = Configuration(search_api=SearchAPI.SEMANTIC_SCHOLAR)
        assert config_s2.search_api == SearchAPI.SEMANTIC_SCHOLAR

        # Test with OpenAI
        config_openai = Configuration(search_api=SearchAPI.OPENAI)
        assert config_openai.search_api == SearchAPI.OPENAI

        # Test with None
        config_none = Configuration(search_api=SearchAPI.NONE)
        assert config_none.search_api == SearchAPI.NONE


class TestToolImports:
    """Test that all tool modules can be imported."""

    def test_import_arxiv_tools(self):
        """Test ArXiv tools can be imported."""
        from research_compass_core.arxiv_tools import (
            arxiv_search,
            arxiv_read_paper,
            get_arxiv_tools,
        )

        assert arxiv_search is not None
        assert arxiv_read_paper is not None
        assert get_arxiv_tools is not None

    def test_import_semantic_scholar_tools(self):
        """Test Semantic Scholar tools can be imported."""
        from research_compass_core.semantic_scholar_tools import (
            semantic_scholar_search,
            semantic_scholar_get_paper,
            get_semantic_scholar_tools,
            SEMANTIC_SCHOLAR_API_BASE,
        )

        assert semantic_scholar_search is not None
        assert semantic_scholar_get_paper is not None
        assert get_semantic_scholar_tools is not None
        assert SEMANTIC_SCHOLAR_API_BASE == "https://api.semanticscholar.org/graph/v1"

    def test_import_configuration(self):
        """Test configuration module can be imported."""
        from research_compass_core.configuration import (
            Configuration,
            SearchAPI,
            ExportFormat,
        )

        assert Configuration is not None
        assert SearchAPI is not None
        assert ExportFormat is not None
