"""Utility functions and helpers for the Research Compass Core agent."""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    MessageLikeRepresentation,
    filter_messages,
)
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from research_compass_core.configuration import Configuration, SearchAPI
from research_compass_core.prompts import summarize_webpage_prompt
from research_compass_core.state import ResearchComplete, Summary

##########################
# Reflection Tool Utils
##########################

@tool(description="Strategic reflection tool for research planning")
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection recorded: {reflection}"

async def summarize_webpage(model: BaseChatModel, webpage_content: str) -> str:
    """Summarize webpage content using AI model with timeout protection.

    Args:
        model: The chat model configured for summarization
        webpage_content: Raw webpage content to be summarized

    Returns:
        Formatted summary with key excerpts, or original content if summarization fails
    """
    try:
        # Create prompt with current date context
        prompt_content = summarize_webpage_prompt.format(
            webpage_content=webpage_content,
            date=get_today_str()
        )

        # Execute summarization with timeout to prevent hanging
        summary = await asyncio.wait_for(
            model.ainvoke([HumanMessage(content=prompt_content)]),
            timeout=60.0  # 60 second timeout for summarization
        )

        # Format the summary with structured sections
        formatted_summary = (
            f"<summary>\n{summary.summary}\n</summary>\n\n"
            f"<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"
        )

        return formatted_summary

    except asyncio.TimeoutError:
        # Timeout during summarization - return original content
        logging.warning("Summarization timed out after 60 seconds, returning original content")
        return webpage_content
    except Exception as e:
        # Other errors during summarization - log and return original content
        logging.warning(f"Summarization failed with error: {str(e)}, returning original content")
        return webpage_content

##########################
# Tool Utils
##########################

async def get_search_tool(search_api: SearchAPI):
    """Configure and return search tools based on the specified API provider.

    Only research paper sources are supported (ArXiv and Semantic Scholar).

    Args:
        search_api: The search API provider to use (ArXiv, Semantic Scholar, or All)

    Returns:
        List of configured search tool objects for the specified provider
    """
    if search_api == SearchAPI.ARXIV:
        # Import and configure ArXiv research tools
        from research_compass_core.arxiv_tools import get_arxiv_tools
        arxiv_tools = get_arxiv_tools()
        # Set metadata for the search tool
        if arxiv_tools:
            arxiv_tools[0].metadata = {
                **(arxiv_tools[0].metadata or {}),
                "type": "search",
                "name": "arxiv_search"
            }
        return arxiv_tools

    elif search_api == SearchAPI.SEMANTIC_SCHOLAR:
        # Import and configure Semantic Scholar research tools
        from research_compass_core.semantic_scholar_tools import get_semantic_scholar_tools
        semantic_scholar_tools = get_semantic_scholar_tools()
        # Set metadata for the search tool
        if semantic_scholar_tools:
            semantic_scholar_tools[0].metadata = {
                **(semantic_scholar_tools[0].metadata or {}),
                "type": "search",
                "name": "semantic_scholar_search"
            }
        return semantic_scholar_tools

    # Default: Use all available academic search APIs (ArXiv + Semantic Scholar)
    # This applies to SearchAPI.ALL and any other value
    from research_compass_core.arxiv_tools import get_arxiv_tools
    from research_compass_core.semantic_scholar_tools import get_semantic_scholar_tools

    all_tools = []

    # Add ArXiv tools
    arxiv_tools = get_arxiv_tools()
    if arxiv_tools:
        arxiv_tools[0].metadata = {
            **(arxiv_tools[0].metadata or {}),
            "type": "search",
            "name": "arxiv_search"
        }
        all_tools.extend(arxiv_tools)

    # Add Semantic Scholar tools
    semantic_scholar_tools = get_semantic_scholar_tools()
    if semantic_scholar_tools:
        semantic_scholar_tools[0].metadata = {
            **(semantic_scholar_tools[0].metadata or {}),
            "type": "search",
            "name": "semantic_scholar_search"
        }
        all_tools.extend(semantic_scholar_tools)

    return all_tools

async def get_all_tools(config: RunnableConfig):
    """Assemble complete toolkit including research and search tools.

    Args:
        config: Runtime configuration specifying search API settings

    Returns:
        List of all configured and available tools for research operations
    """
    # Start with core research tools
    tools = [tool(ResearchComplete), think_tool]

    # Add configured search tools
    configurable = Configuration.from_runnable_config(config)
    search_api = SearchAPI(get_config_value(configurable.search_api))
    search_tools = await get_search_tool(search_api)
    tools.extend(search_tools)

    return tools

def get_notes_from_tool_calls(messages: list[MessageLikeRepresentation]):
    """Extract notes from tool call messages."""
    return [tool_msg.content for tool_msg in filter_messages(messages, include_types="tool")]

##########################
# Model Provider Native Websearch Utils
##########################

def openai_websearch_called(response):
    """Detect if OpenAI's web search functionality was used in the response.

    Args:
        response: The response object from OpenAI's API

    Returns:
        True if web search was called, False otherwise
    """
    # Check for tool outputs in the response metadata
    tool_outputs = response.additional_kwargs.get("tool_outputs")
    if not tool_outputs:
        return False

    # Look for web search calls in the tool outputs
    for tool_output in tool_outputs:
        if tool_output.get("type") == "web_search_call":
            return True

    return False


##########################
# Token Limit Exceeded Utils
##########################

def is_token_limit_exceeded(exception: Exception, model_name: str = None) -> bool:
    """Determine if an exception indicates a token/context limit was exceeded.

    Args:
        exception: The exception to analyze
        model_name: Optional model name to optimize provider detection

    Returns:
        True if the exception indicates a token limit was exceeded, False otherwise
    """
    error_str = str(exception).lower()

    # Check OpenAI token limit patterns
    return _check_openai_token_limit(exception, error_str)

def _check_openai_token_limit(exception: Exception, error_str: str) -> bool:
    """Check if exception indicates OpenAI token limit exceeded."""
    # Analyze exception metadata
    exception_type = str(type(exception))
    class_name = exception.__class__.__name__
    module_name = getattr(exception.__class__, '__module__', '')

    # Check if this is an OpenAI exception
    is_openai_exception = (
        'openai' in exception_type.lower() or
        'openai' in module_name.lower()
    )

    # Check for typical OpenAI token limit error types
    is_request_error = class_name in ['BadRequestError', 'InvalidRequestError']

    if is_openai_exception and is_request_error:
        # Look for token-related keywords in error message
        token_keywords = ['token', 'context', 'length', 'maximum context', 'reduce']
        if any(keyword in error_str for keyword in token_keywords):
            return True

    # Check for specific OpenAI error codes
    if hasattr(exception, 'code') and hasattr(exception, 'type'):
        error_code = getattr(exception, 'code', '')
        error_type = getattr(exception, 'type', '')

        if (error_code == 'context_length_exceeded' or
            error_type == 'invalid_request_error'):
            return True

    return False

# NOTE: This may be out of date or not applicable to your models. Please update this as needed.
MODEL_TOKEN_LIMITS = {
    "openai:gpt-4.1-mini": 1047576,
    "openai:gpt-4.1-nano": 1047576,
    "openai:gpt-4.1": 1047576,
    "openai:gpt-4o-mini": 128000,
    "openai:gpt-4o": 128000,
    "openai:o4-mini": 200000,
    "openai:o3-mini": 200000,
    "openai:o3": 200000,
    "openai:o3-pro": 200000,
    "openai:o1": 200000,
    "openai:o1-pro": 200000,
}

def get_model_token_limit(model_string):
    """Look up the token limit for a specific model.

    Args:
        model_string: The model identifier string to look up

    Returns:
        Token limit as integer if found, None if model not in lookup table
    """
    # Search through known model token limits
    for model_key, token_limit in MODEL_TOKEN_LIMITS.items():
        if model_key in model_string:
            return token_limit

    # Model not found in lookup table
    return None

def remove_up_to_last_ai_message(messages: list[MessageLikeRepresentation]) -> list[MessageLikeRepresentation]:
    """Truncate message history by removing up to the last AI message.

    This is useful for handling token limit exceeded errors by removing recent context.

    Args:
        messages: List of message objects to truncate

    Returns:
        Truncated message list up to (but not including) the last AI message
    """
    # Search backwards through messages to find the last AI message
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], AIMessage):
            # Return everything up to (but not including) the last AI message
            return messages[:i]

    # No AI messages found, return original list
    return messages

##########################
# Misc Utils
##########################

def get_today_str() -> str:
    """Get current date formatted for display in prompts and outputs.

    Returns:
        Human-readable date string in format like 'Mon Jan 15, 2024'
    """
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"

def get_config_value(value):
    """Extract value from configuration, handling enums and None values."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        return value
    else:
        return value.value

def get_api_key_for_model(model_name: str, config: RunnableConfig):
    """Get API key for OpenAI models from environment or config."""
    should_get_from_config = os.getenv("GET_API_KEYS_FROM_CONFIG", "false")
    model_name = model_name.lower()
    if should_get_from_config.lower() == "true":
        api_keys = config.get("configurable", {}).get("apiKeys", {})
        if not api_keys:
            return None
        if model_name.startswith("openai:"):
            return api_keys.get("OPENAI_API_KEY")
        return None
    else:
        if model_name.startswith("openai:"):
            return os.getenv("OPENAI_API_KEY")
        return None

##########################
# Source Extraction Utils
##########################

def extract_sources_from_messages(messages: List[MessageLikeRepresentation]) -> List:
    """Extract PaperSource objects from tool messages containing paper metadata.

    Parses outputs from arxiv_search and semantic_scholar_search tools to create
    structured PaperSource objects for citation tracking.

    Args:
        messages: List of messages including tool outputs

    Returns:
        List of PaperSource objects extracted from search tool outputs
    """
    import re
    import uuid
    from langchain_core.messages import ToolMessage
    from research_compass_core.state import PaperSource

    sources = []
    seen_urls = set()  # Deduplicate by URL

    # Filter for tool messages
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]

    print(f"\n📋 EXTRACT_SOURCES: Total messages: {len(messages)}, Tool messages: {len(tool_messages)}")
    logging.info(f"extract_sources_from_messages: Processing {len(tool_messages)} tool messages")

    # Log ALL tool names found
    tool_names = [getattr(msg, 'name', 'unknown') for msg in tool_messages]
    print(f"📋 EXTRACT_SOURCES: Tool names found: {tool_names}")
    logging.info(f"Tool names found: {tool_names}")

    for tool_msg in tool_messages:
        tool_name = getattr(tool_msg, 'name', '')
        content = str(tool_msg.content)

        logging.info(f"Processing tool message: '{tool_name}' (length: {len(content)} chars)")

        # Debug: Print first 500 chars of content to see what we're working with
        if content and len(content) > 100:
            logging.info(f"Content preview: {content[:500]}")

        # Parse ArXiv search results
        if tool_name == 'arxiv_search':
            arxiv_sources = _parse_arxiv_sources(content, seen_urls)
            logging.info(f"Parsed {len(arxiv_sources)} ArXiv sources")
            sources.extend(arxiv_sources)

        # Parse Semantic Scholar search results
        elif tool_name == 'semantic_scholar_search':
            ss_sources = _parse_semantic_scholar_sources(content, seen_urls)
            logging.info(f"Parsed {len(ss_sources)} Semantic Scholar sources")
            sources.extend(ss_sources)

    print(f"📋 EXTRACT_SOURCES: Total {len(sources)} sources extracted\n")
    logging.info(f"extract_sources_from_messages: Total {len(sources)} sources extracted")
    return sources

def _parse_arxiv_sources(content: str, seen_urls: set) -> List:
    """Parse ArXiv tool output to extract PaperSource objects."""
    import re
    import uuid
    from research_compass_core.state import PaperSource

    sources = []
    # Split by paper separator
    paper_blocks = re.split(r'-{80,}', content)

    logging.info(f"_parse_arxiv_sources: Found {len(paper_blocks)} blocks")

    for i, block in enumerate(paper_blocks):
        if '--- PAPER' not in block:
            continue

        logging.info(f"_parse_arxiv_sources: Processing block {i} with PAPER marker")

        try:
            # Extract title
            title_match = re.search(r'--- PAPER \d+: (.+?) ---', block)
            title = title_match.group(1).strip() if title_match else ""

            # Extract authors
            authors_match = re.search(r'Authors: (.+?)(?:\n|$)', block)
            authors_str = authors_match.group(1).strip() if authors_match else ""
            # Parse author names, handling "et al."
            if 'et al.' in authors_str:
                authors_str = authors_str.split('et al.')[0]
            authors = [a.strip() for a in authors_str.split(',') if a.strip()]

            # Extract published date
            published_match = re.search(r'Published: ([\d-]+)', block)
            published_date = published_match.group(1) if published_match else None

            # Extract URL
            url_match = re.search(r'URL: (https?://[^\s]+)', block)
            url = url_match.group(1).strip() if url_match else ""

            # Extract PDF URL
            pdf_match = re.search(r'PDF: (https?://[^\s]+)', block)
            pdf_url = pdf_match.group(1).strip() if pdf_match else None

            # Extract abstract
            abstract_match = re.search(r'ABSTRACT:\s*(.+?)(?:SEARCH QUERY:|$)', block, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else ""

            # Extract ArXiv ID from URL
            arxiv_id = url.split('/')[-1] if url else None

            # Skip if already seen
            if url in seen_urls or not url:
                logging.info(f"Skipping paper - already seen or no URL: {title[:50] if title else 'No title'}")
                continue

            seen_urls.add(url)

            # Create PaperSource
            source = PaperSource(
                source_id=str(uuid.uuid4()),
                paper_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                published_date=published_date,
                search_api="arxiv",
                accessed_at=datetime.now().isoformat()
            )
            sources.append(source)
            logging.info(f"Successfully parsed ArXiv source: {title[:50]}")

        except Exception as e:
            logging.warning(f"Failed to parse ArXiv source: {str(e)}")
            import traceback
            logging.warning(f"Traceback: {traceback.format_exc()}")
            continue

    logging.info(f"_parse_arxiv_sources: Returning {len(sources)} sources")
    return sources

def _parse_semantic_scholar_sources(content: str, seen_urls: set) -> List:
    """Parse Semantic Scholar tool output to extract PaperSource objects."""
    import re
    import uuid
    from research_compass_core.state import PaperSource

    sources = []
    # Split by paper separator (uses same --- format as ArXiv)
    paper_blocks = re.split(r'-{80,}', content)

    logging.info(f"_parse_semantic_scholar_sources: Found {len(paper_blocks)} blocks")

    for i, block in enumerate(paper_blocks):
        if '--- PAPER' not in block:
            continue

        logging.info(f"_parse_semantic_scholar_sources: Processing block {i} with PAPER marker")

        try:
            # Extract title
            title_match = re.search(r'--- PAPER \d+: (.+?) ---', block)
            title = title_match.group(1).strip() if title_match else ""

            # Extract authors
            authors_match = re.search(r'Authors: (.+?)(?:\n|$)', block)
            authors_str = authors_match.group(1).strip() if authors_match else ""
            if 'et al.' in authors_str:
                authors_str = authors_str.split('et al.')[0]
            authors = [a.strip() for a in authors_str.split(',') if a.strip()]

            # Extract year and venue (on same line: "Year: 2023 | Venue: Conference")
            year_match = re.search(r'Year: ([^\n|]+)', block)
            year_str = year_match.group(1).strip() if year_match else None
            # Extract just the year number if it's not "Unknown year"
            year = None
            if year_str and year_str != "Unknown year":
                year_num_match = re.search(r'\d{4}', year_str)
                year = year_num_match.group(0) if year_num_match else None

            # Extract venue
            venue_match = re.search(r'Venue: ([^\n]+)', block)
            venue = venue_match.group(1).strip() if venue_match else None
            if venue and (venue.lower() in ['unknown venue', 'none']):
                venue = None

            # Extract citation count
            citations_match = re.search(r'Citations: (\d+)', block)
            citation_count = int(citations_match.group(1)) if citations_match else None

            # Extract URL
            url_match = re.search(r'URL: (https?://[^\s]+)', block)
            url = url_match.group(1).strip() if url_match else ""

            # Extract PDF URL (optional line)
            pdf_match = re.search(r'PDF: (https?://[^\s]+)', block)
            pdf_url = pdf_match.group(1).strip() if pdf_match else None

            # Extract abstract
            abstract_match = re.search(r'ABSTRACT:\s*(.+?)(?:SEARCH QUERY:|PAPER ID:|$)', block, re.DOTALL)
            abstract = abstract_match.group(1).strip() if abstract_match else ""

            # Extract Semantic Scholar paper ID
            paper_id_match = re.search(r'PAPER ID: ([^\s\n]+)', block)
            paper_id = paper_id_match.group(1).strip() if paper_id_match else None

            # Skip if already seen
            if url in seen_urls or not url:
                logging.info(f"Skipping paper - already seen or no URL: {title[:50] if title else 'No title'}")
                continue

            seen_urls.add(url)

            # Create PaperSource
            source = PaperSource(
                source_id=str(uuid.uuid4()),
                paper_id=paper_id,
                title=title,
                authors=authors,
                abstract=abstract,
                url=url,
                pdf_url=pdf_url,
                published_date=year,
                citation_count=citation_count,
                venue=venue,
                search_api="semantic_scholar",
                accessed_at=datetime.now().isoformat()
            )
            sources.append(source)
            logging.info(f"Successfully parsed Semantic Scholar source: {title[:50]}")

        except Exception as e:
            logging.warning(f"Failed to parse Semantic Scholar source: {str(e)}")
            import traceback
            logging.warning(f"Traceback: {traceback.format_exc()}")
            continue

    logging.info(f"_parse_semantic_scholar_sources: Returning {len(sources)} sources")
    return sources
