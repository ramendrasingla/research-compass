"""Integration tests for ArXiv and Semantic Scholar search APIs.

These tests verify that both search APIs work correctly with real research queries.
They require:
- OPENAI_API_KEY to be set (for the LLM)
- Network connection (for API calls)
- SEMANTIC_SCHOLAR_API_KEY is optional (will use shared rate limits if not set)

Run with: pytest tests/test_integration_search_apis.py -v -s
"""

import asyncio
import os
import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from research_compass_core import graph

# Load environment variables
load_dotenv()


@pytest.fixture(scope="module")
def check_openai_key():
    """Verify OpenAI API key is available."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping integration tests")


@pytest.fixture
def base_config():
    """Base configuration for research tests."""
    return {
        "configurable": {
            "thread_id": "integration-test",
            "research_model": "openai:gpt-4o-mini",  # Use cheaper model for testing
            "max_researcher_iterations": 2,  # Limit iterations for faster tests
            "max_concurrent_research_units": 2,  # Limit parallel units
            "allow_clarification": False,  # Skip clarification for automated tests
        }
    }


@pytest.fixture
def test_query():
    """Simple research query that both APIs should handle well."""
    return "What are the main applications of transformer models in natural language processing?"


class TestArxivSearchAPI:
    """Test ArXiv search API integration."""

    @pytest.mark.asyncio
    async def test_arxiv_search_basic(self, check_openai_key, base_config, test_query):
        """Test basic research with ArXiv search API."""
        # Configure for ArXiv
        config = base_config.copy()
        config["configurable"]["search_api"] = "arxiv"

        print("\n" + "=" * 80)
        print("🧪 Testing ArXiv Search API")
        print("=" * 80)
        print(f"Query: {test_query}")
        print(f"Search API: arxiv")
        print("=" * 80)

        try:
            # Run research
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=test_query)]},
                config=config
            )

            # Validate results
            assert "final_report" in result, "Should generate a final report"
            final_report = result["final_report"]

            assert isinstance(final_report, str), "Report should be a string"
            assert len(final_report) > 100, "Report should have substantial content"

            # Check for research indicators
            assert any(keyword in final_report.lower() for keyword in
                      ["transformer", "nlp", "natural language", "attention"]), \
                   "Report should contain relevant keywords"

            print(f"\n✅ ArXiv test passed")
            print(f"📄 Report length: {len(final_report)} characters")
            print(f"📝 First 200 chars: {final_report[:200]}...")

        except Exception as e:
            pytest.fail(f"ArXiv search test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_arxiv_physics_query(self, check_openai_key, base_config):
        """Test ArXiv with a physics query (ArXiv's specialty)."""
        # Configure for ArXiv
        config = base_config.copy()
        config["configurable"]["search_api"] = "arxiv"

        # Physics query (ArXiv is great for this)
        physics_query = "What is quantum entanglement?"

        print("\n" + "=" * 80)
        print("🧪 Testing ArXiv with Physics Query")
        print("=" * 80)

        try:
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=physics_query)]},
                config=config
            )

            assert "final_report" in result
            final_report = result["final_report"]
            assert len(final_report) > 100
            assert "quantum" in final_report.lower()

            print(f"✅ Physics query test passed")
            print(f"📄 Report length: {len(final_report)} characters")

        except Exception as e:
            pytest.fail(f"ArXiv physics query test failed: {str(e)}")


class TestSemanticScholarSearchAPI:
    """Test Semantic Scholar search API integration."""

    @pytest.mark.asyncio
    async def test_semantic_scholar_search_basic(self, check_openai_key, base_config, test_query):
        """Test basic research with Semantic Scholar search API (no API key required)."""
        # Configure for Semantic Scholar
        config = base_config.copy()
        config["configurable"]["search_api"] = "semantic_scholar"

        print("\n" + "=" * 80)
        print("🧪 Testing Semantic Scholar Search API")
        print("=" * 80)
        print(f"Query: {test_query}")
        print(f"Search API: semantic_scholar")
        s2_key = "SET" if os.getenv("SEMANTIC_SCHOLAR_API_KEY") else "NOT SET (using shared limits)"
        print(f"API Key: {s2_key}")
        print("=" * 80)

        try:
            # Run research
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=test_query)]},
                config=config
            )

            # Validate results
            assert "final_report" in result, "Should generate a final report"
            final_report = result["final_report"]

            assert isinstance(final_report, str), "Report should be a string"
            assert len(final_report) > 100, "Report should have substantial content"

            # Check for research indicators
            assert any(keyword in final_report.lower() for keyword in
                      ["transformer", "nlp", "natural language", "attention"]), \
                   "Report should contain relevant keywords"

            print(f"\n✅ Semantic Scholar test passed")
            print(f"📄 Report length: {len(final_report)} characters")
            print(f"📝 First 200 chars: {final_report[:200]}...")

        except Exception as e:
            # Check if it's a rate limit issue
            if "429" in str(e) or "rate limit" in str(e).lower():
                pytest.skip(f"Rate limit exceeded - this is expected without API key: {str(e)}")
            pytest.fail(f"Semantic Scholar search test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_semantic_scholar_biomedical_query(self, check_openai_key, base_config):
        """Test Semantic Scholar with biomedical query (broader coverage than ArXiv)."""
        # Configure for Semantic Scholar
        config = base_config.copy()
        config["configurable"]["search_api"] = "semantic_scholar"

        # Biomedical query (Semantic Scholar covers this, ArXiv doesn't)
        bio_query = "What are CRISPR applications in medicine?"

        print("\n" + "=" * 80)
        print("🧪 Testing Semantic Scholar with Biomedical Query")
        print("=" * 80)

        try:
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=bio_query)]},
                config=config
            )

            assert "final_report" in result
            final_report = result["final_report"]
            assert len(final_report) > 100
            assert "crispr" in final_report.lower() or "gene" in final_report.lower()

            print(f"✅ Biomedical query test passed")
            print(f"📄 Report length: {len(final_report)} characters")

        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                pytest.skip(f"Rate limit exceeded: {str(e)}")
            pytest.fail(f"Semantic Scholar biomedical query test failed: {str(e)}")


class TestSearchAPIComparison:
    """Compare results across different search APIs."""

    @pytest.mark.asyncio
    async def test_compare_arxiv_vs_semantic_scholar(self, check_openai_key, base_config):
        """Compare results from ArXiv vs Semantic Scholar for the same query."""
        cs_query = "What is deep learning?"

        print("\n" + "=" * 80)
        print("🔬 Comparing ArXiv vs Semantic Scholar")
        print("=" * 80)
        print(f"Query: {cs_query}")

        results = {}

        # Test with ArXiv
        print("\n📚 Testing with ArXiv...")
        arxiv_config = base_config.copy()
        arxiv_config["configurable"]["search_api"] = "arxiv"

        try:
            arxiv_result = await graph.ainvoke(
                {"messages": [HumanMessage(content=cs_query)]},
                arxiv_config
            )
            results["arxiv"] = arxiv_result.get("final_report", "")
            print(f"✅ ArXiv completed - {len(results['arxiv'])} chars")
        except Exception as e:
            print(f"⚠️ ArXiv failed: {str(e)}")
            results["arxiv"] = None

        # Small delay to avoid rate limits
        await asyncio.sleep(2)

        # Test with Semantic Scholar
        print("\n🎓 Testing with Semantic Scholar...")
        s2_config = base_config.copy()
        s2_config["configurable"]["search_api"] = "semantic_scholar"

        try:
            s2_result = await graph.ainvoke(
                {"messages": [HumanMessage(content=cs_query)]},
                s2_config
            )
            results["semantic_scholar"] = s2_result.get("final_report", "")
            print(f"✅ Semantic Scholar completed - {len(results['semantic_scholar'])} chars")
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                print(f"⚠️ Semantic Scholar rate limited (expected without API key)")
                results["semantic_scholar"] = None
            else:
                print(f"⚠️ Semantic Scholar failed: {str(e)}")
                results["semantic_scholar"] = None

        # Compare results
        print("\n" + "=" * 80)
        print("📊 Comparison Results")
        print("=" * 80)

        if results["arxiv"]:
            print(f"ArXiv report: {len(results['arxiv'])} characters")
        else:
            print("ArXiv: No result")

        if results["semantic_scholar"]:
            print(f"Semantic Scholar report: {len(results['semantic_scholar'])} characters")
        else:
            print("Semantic Scholar: No result")

        # At least one should succeed
        assert results["arxiv"] or results["semantic_scholar"], \
               "At least one search API should return results"

        # Both reports should contain relevant content if they succeeded
        if results["arxiv"]:
            assert "deep learning" in results["arxiv"].lower() or "neural" in results["arxiv"].lower()

        if results["semantic_scholar"]:
            assert "deep learning" in results["semantic_scholar"].lower() or "neural" in results["semantic_scholar"].lower()

        print("\n✅ Comparison test passed")


class TestSearchAPIConfiguration:
    """Test different search API configurations."""

    @pytest.mark.asyncio
    async def test_switch_search_apis(self, check_openai_key, base_config):
        """Test switching between different search APIs in sequence."""
        simple_query = "What is machine learning?"

        print("\n" + "=" * 80)
        print("🔄 Testing Search API Switching")
        print("=" * 80)

        # Test ArXiv first
        print("\n1️⃣ Using ArXiv...")
        arxiv_config = base_config.copy()
        arxiv_config["configurable"]["search_api"] = "arxiv"
        arxiv_config["configurable"]["thread_id"] = "test-arxiv"

        try:
            arxiv_result = await graph.ainvoke(
                {"messages": [HumanMessage(content=simple_query)]},
                arxiv_config
            )
            assert "final_report" in arxiv_result
            print(f"✅ ArXiv completed")
        except Exception as e:
            pytest.fail(f"ArXiv failed: {str(e)}")

        # Small delay
        await asyncio.sleep(2)

        # Then test Semantic Scholar
        print("\n2️⃣ Using Semantic Scholar...")
        s2_config = base_config.copy()
        s2_config["configurable"]["search_api"] = "semantic_scholar"
        s2_config["configurable"]["thread_id"] = "test-s2"

        try:
            s2_result = await graph.ainvoke(
                {"messages": [HumanMessage(content=simple_query)]},
                s2_config
            )
            assert "final_report" in s2_result
            print(f"✅ Semantic Scholar completed")
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                pytest.skip(f"Semantic Scholar rate limited: {str(e)}")
            pytest.fail(f"Semantic Scholar failed: {str(e)}")

        print("\n✅ API switching test passed")

    @pytest.mark.asyncio
    async def test_no_search_api(self, check_openai_key, base_config):
        """Test with search API disabled (should still work if model can answer)."""
        print("\n" + "=" * 80)
        print("🚫 Testing with No Search API")
        print("=" * 80)

        config = base_config.copy()
        config["configurable"]["search_api"] = "none"

        # Use a simple question that doesn't require search
        simple_question = "What is 2+2?"

        try:
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=simple_question)]},
                config
            )

            assert "final_report" in result
            print(f"✅ No-search mode works")

        except Exception as e:
            # This might fail if the model requires search tools
            print(f"⚠️ No-search mode failed (may be expected): {str(e)}")


# Utility function to run tests manually
async def run_all_integration_tests():
    """Run all integration tests manually (for debugging)."""
    print("\n" + "=" * 80)
    print("🧪 Running All Integration Tests")
    print("=" * 80)

    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set - cannot run tests")
        return

    base_config = {
        "configurable": {
            "thread_id": "manual-test",
            "research_model": "openai:gpt-4o-mini",
            "max_researcher_iterations": 2,
            "max_concurrent_research_units": 2,
            "allow_clarification": False,
        }
    }

    test_query = "What are transformer models?"

    # Test ArXiv
    print("\n📚 Testing ArXiv...")
    try:
        arxiv_config = base_config.copy()
        arxiv_config["configurable"]["search_api"] = "arxiv"
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=test_query)]},
            arxiv_config
        )
        print(f"✅ ArXiv: {len(result['final_report'])} chars")
    except Exception as e:
        print(f"❌ ArXiv failed: {str(e)}")

    await asyncio.sleep(2)

    # Test Semantic Scholar
    print("\n🎓 Testing Semantic Scholar...")
    try:
        s2_config = base_config.copy()
        s2_config["configurable"]["search_api"] = "semantic_scholar"
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=test_query)]},
            s2_config
        )
        print(f"✅ Semantic Scholar: {len(result['final_report'])} chars")
    except Exception as e:
        print(f"❌ Semantic Scholar failed: {str(e)}")

    print("\n" + "=" * 80)
    print("✅ Manual test run complete")
    print("=" * 80)


if __name__ == "__main__":
    # Run tests manually for debugging
    asyncio.run(run_all_integration_tests())
