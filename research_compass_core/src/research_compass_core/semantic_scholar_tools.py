"""Semantic Scholar search and retrieval tools for deep research."""

import asyncio
import logging
import os
from typing import List, Optional
from datetime import datetime

import httpx
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing import Annotated

##########################
# Semantic Scholar API Configuration
##########################

SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
SEMANTIC_SCHOLAR_TIMEOUT = 30.0  # seconds

# Default fields to retrieve for paper search
DEFAULT_SEARCH_FIELDS = [
    "paperId",
    "title",
    "abstract",
    "year",
    "authors",
    "citationCount",
    "url",
    "publicationTypes",
    "publicationDate",
    "openAccessPdf",
    "venue",
    "fieldsOfStudy",
]

##########################
# Semantic Scholar Search Tool
##########################

SEMANTIC_SCHOLAR_SEARCH_DESCRIPTION = (
    "Search Semantic Scholar for academic research papers across 200+ million papers from all disciplines. "
    "Use this to find papers on specific topics, authors, concepts, or research areas. "
    "Returns paper titles, authors, abstracts, citations, and URLs. "
    "This covers a much broader range of academic sources than arXiv (which is physics/CS/math only)."
)


@tool(description=SEMANTIC_SCHOLAR_SEARCH_DESCRIPTION)
async def semantic_scholar_search(
    queries: List[str],
    max_results: Annotated[int, InjectedToolArg] = 10,
    min_citation_count: Annotated[Optional[int], InjectedToolArg] = None,
    year_range: Annotated[Optional[str], InjectedToolArg] = None,
    config: RunnableConfig = None
) -> str:
    """Search Semantic Scholar for research papers and retrieve their metadata and abstracts.

    Args:
        queries: List of search queries to execute (e.g., ["deep learning", "CRISPR gene editing"])
        max_results: Maximum number of results to return per query (default: 10)
        min_citation_count: Minimum number of citations (default: None for no filter)
        year_range: Year filter like "2020-2024" or "2023-" (default: None for all years)
        config: Runtime configuration

    Returns:
        Formatted string containing paper information including title, authors, abstract, citations, and URL
    """
    # Get API key from environment if available (optional but recommended)
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    # Execute all queries
    all_results = []

    async with httpx.AsyncClient(timeout=SEMANTIC_SCHOLAR_TIMEOUT) as client:
        for query in queries:
            try:
                # Build query parameters
                params = {
                    "query": query,
                    "fields": ",".join(DEFAULT_SEARCH_FIELDS),
                    "limit": max_results,
                }

                # Add optional filters
                if min_citation_count is not None:
                    params["minCitationCount"] = min_citation_count
                if year_range:
                    params["year"] = year_range

                # Use bulk search endpoint (recommended by Semantic Scholar)
                url = f"{SEMANTIC_SCHOLAR_API_BASE}/paper/search/bulk"

                # Execute search
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                # Parse results
                data = response.json()
                papers = data.get("data", [])

                for paper in papers:
                    # Extract authors
                    authors_list = paper.get("authors", [])
                    author_names = [author.get("name", "Unknown") for author in authors_list]

                    # Extract open access PDF if available
                    pdf_info = paper.get("openAccessPdf")
                    pdf_url = pdf_info.get("url") if pdf_info else None

                    all_results.append({
                        "query": query,
                        "paper_id": paper.get("paperId", ""),
                        "title": paper.get("title", "No title"),
                        "authors": author_names,
                        "abstract": paper.get("abstract", "No abstract available"),
                        "year": paper.get("year"),
                        "publication_date": paper.get("publicationDate"),
                        "citation_count": paper.get("citationCount", 0),
                        "url": paper.get("url", ""),
                        "pdf_url": pdf_url,
                        "venue": paper.get("venue", "Unknown venue"),
                        "fields_of_study": paper.get("fieldsOfStudy", []),
                        "publication_types": paper.get("publicationTypes", []),
                    })

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logging.warning(f"Semantic Scholar rate limit exceeded for query '{query}'. Consider using an API key for higher limits.")
                else:
                    logging.warning(f"Semantic Scholar search failed for query '{query}': HTTP {e.response.status_code}")
                continue
            except Exception as e:
                logging.warning(f"Semantic Scholar search failed for query '{query}': {str(e)}")
                continue

    # Format the results
    if not all_results:
        return "No papers found on Semantic Scholar for the given queries. Try different search terms or broader topics."

    formatted_output = f"Found {len(all_results)} papers on Semantic Scholar:\n\n"

    for i, paper in enumerate(all_results, 1):
        # Format authors
        authors_str = ", ".join(paper["authors"][:3])  # Show first 3 authors
        if len(paper["authors"]) > 3:
            authors_str += f" et al. ({len(paper['authors'])} authors total)"

        # Format publication info
        year_str = str(paper["year"]) if paper["year"] else "Unknown year"
        venue_str = paper["venue"] if paper["venue"] else "Unknown venue"

        formatted_output += f"--- PAPER {i}: {paper['title']} ---\n"
        formatted_output += f"Authors: {authors_str}\n"
        formatted_output += f"Year: {year_str} | Venue: {venue_str}\n"
        formatted_output += f"Citations: {paper['citation_count']}\n"

        # Add fields of study if available
        if paper["fields_of_study"]:
            fields_str = ", ".join(paper["fields_of_study"][:5])
            formatted_output += f"Fields: {fields_str}\n"

        formatted_output += f"URL: {paper['url']}\n"

        # Add PDF link if available
        if paper["pdf_url"]:
            formatted_output += f"PDF: {paper['pdf_url']}\n"

        formatted_output += f"\nABSTRACT:\n{paper['abstract']}\n\n"
        formatted_output += f"SEARCH QUERY: {paper['query']}\n"
        formatted_output += f"PAPER ID: {paper['paper_id']}\n"
        formatted_output += "-" * 80 + "\n\n"

    return formatted_output


##########################
# Semantic Scholar Paper Details Tool
##########################

SEMANTIC_SCHOLAR_GET_PAPER_DESCRIPTION = (
    "Get detailed information about a specific paper from Semantic Scholar using its paper ID. "
    "Use this when you have a Semantic Scholar paper ID and need more details about that specific paper. "
    "Returns comprehensive paper information including full abstract, citations, references, and metadata."
)


@tool(description=SEMANTIC_SCHOLAR_GET_PAPER_DESCRIPTION)
async def semantic_scholar_get_paper(
    paper_ids: List[str],
    config: RunnableConfig = None
) -> str:
    """Get detailed information about specific papers from Semantic Scholar.

    Args:
        paper_ids: List of Semantic Scholar paper IDs (e.g., ["649def34f8be52c8b66281af98ae884c09aef38b"])
        config: Runtime configuration

    Returns:
        Formatted string containing detailed paper information
    """
    # Get API key from environment if available
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    # Fields to retrieve for detailed paper view
    detail_fields = [
        "paperId",
        "title",
        "abstract",
        "year",
        "authors",
        "citationCount",
        "referenceCount",
        "url",
        "publicationTypes",
        "publicationDate",
        "openAccessPdf",
        "venue",
        "fieldsOfStudy",
        "influentialCitationCount",
    ]

    all_papers = []

    async with httpx.AsyncClient(timeout=SEMANTIC_SCHOLAR_TIMEOUT) as client:
        for paper_id in paper_ids:
            try:
                # Build URL for paper details
                url = f"{SEMANTIC_SCHOLAR_API_BASE}/paper/{paper_id}"
                params = {"fields": ",".join(detail_fields)}

                # Execute request
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                # Parse paper data
                paper = response.json()

                # Extract authors
                authors_list = paper.get("authors", [])
                author_names = [author.get("name", "Unknown") for author in authors_list]

                # Extract open access PDF if available
                pdf_info = paper.get("openAccessPdf")
                pdf_url = pdf_info.get("url") if pdf_info else None

                all_papers.append({
                    "paper_id": paper.get("paperId", paper_id),
                    "title": paper.get("title", "No title"),
                    "authors": author_names,
                    "abstract": paper.get("abstract", "No abstract available"),
                    "year": paper.get("year"),
                    "publication_date": paper.get("publicationDate"),
                    "citation_count": paper.get("citationCount", 0),
                    "influential_citation_count": paper.get("influentialCitationCount", 0),
                    "reference_count": paper.get("referenceCount", 0),
                    "url": paper.get("url", ""),
                    "pdf_url": pdf_url,
                    "venue": paper.get("venue", "Unknown venue"),
                    "fields_of_study": paper.get("fieldsOfStudy", []),
                    "publication_types": paper.get("publicationTypes", []),
                })

            except httpx.HTTPStatusError as e:
                logging.warning(f"Failed to get paper {paper_id}: HTTP {e.response.status_code}")
                all_papers.append({
                    "paper_id": paper_id,
                    "title": "ERROR",
                    "authors": [],
                    "abstract": f"Error retrieving paper: HTTP {e.response.status_code}",
                    "year": None,
                    "citation_count": 0,
                })
            except Exception as e:
                logging.warning(f"Failed to get paper {paper_id}: {str(e)}")
                all_papers.append({
                    "paper_id": paper_id,
                    "title": "ERROR",
                    "authors": [],
                    "abstract": f"Error retrieving paper: {str(e)}",
                    "year": None,
                    "citation_count": 0,
                })

    # Format output
    if not all_papers:
        return "Failed to retrieve any papers. Please check the paper IDs and try again."

    formatted_output = ""
    for i, paper in enumerate(all_papers, 1):
        authors_str = ", ".join(paper["authors"][:5])
        if len(paper["authors"]) > 5:
            authors_str += f" et al. ({len(paper['authors'])} authors total)"

        year_str = str(paper["year"]) if paper.get("year") else "Unknown year"
        venue_str = paper.get("venue", "Unknown venue")

        formatted_output += f"\n\n{'=' * 80}\n"
        formatted_output += f"PAPER {i}: {paper['title']}\n"
        formatted_output += f"{'=' * 80}\n"
        formatted_output += f"Semantic Scholar ID: {paper['paper_id']}\n"
        formatted_output += f"Authors: {authors_str}\n"
        formatted_output += f"Year: {year_str} | Venue: {venue_str}\n"
        formatted_output += f"Citations: {paper.get('citation_count', 0)}"

        if paper.get("influential_citation_count"):
            formatted_output += f" (Influential: {paper['influential_citation_count']})"

        formatted_output += f"\nReferences: {paper.get('reference_count', 0)}\n"

        # Add fields of study if available
        if paper.get("fields_of_study"):
            fields_str = ", ".join(paper["fields_of_study"])
            formatted_output += f"Fields: {fields_str}\n"

        formatted_output += f"URL: {paper.get('url', 'N/A')}\n"

        # Add PDF link if available
        if paper.get("pdf_url"):
            formatted_output += f"PDF: {paper['pdf_url']}\n"

        formatted_output += f"\nABSTRACT:\n{paper['abstract']}\n"
        formatted_output += f"{'=' * 80}\n\n"

    return formatted_output


##########################
# Get Semantic Scholar Tools
##########################

def get_semantic_scholar_tools():
    """Get all Semantic Scholar research tools.

    Returns:
        List of Semantic Scholar tools for research
    """
    return [semantic_scholar_search, semantic_scholar_get_paper]
