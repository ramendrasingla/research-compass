"""ArXiv search and retrieval tools for deep research."""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

import arxiv
import pymupdf
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing import Annotated

##########################
# ArXiv Search Tool
##########################

ARXIV_SEARCH_DESCRIPTION = (
    "Search arXiv for academic research papers. "
    "Use this to find papers on specific topics, authors, or research areas. "
    "Returns paper titles, authors, abstracts, and URLs."
)


@tool(description=ARXIV_SEARCH_DESCRIPTION)
async def arxiv_search(
    queries: List[str],
    max_results: Annotated[int, InjectedToolArg] = 5,
    sort_by: Annotated[str, InjectedToolArg] = "relevance",
    config: RunnableConfig = None
) -> str:
    """Search arXiv for research papers and retrieve their metadata and abstracts.

    Args:
        queries: List of search queries to execute (e.g., ["quantum computing", "machine learning transformers"])
        max_results: Maximum number of results to return per query (default: 5)
        sort_by: Sort results by 'relevance', 'lastUpdatedDate', or 'submittedDate' (default: 'relevance')
        config: Runtime configuration

    Returns:
        Formatted string containing paper information including title, authors, abstract, and URL
    """
    # Map string sort parameter to arxiv SortCriterion
    sort_criterion_map = {
        "relevance": arxiv.SortCriterion.Relevance,
        "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
        "submittedDate": arxiv.SortCriterion.SubmittedDate,
    }
    sort_criterion = sort_criterion_map.get(sort_by, arxiv.SortCriterion.Relevance)

    # Execute all queries
    all_results = []

    for query in queries:
        try:
            # Create search client
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_criterion
            )

            # Fetch results (convert to list to execute the search)
            results = list(search.results())

            for result in results:
                all_results.append({
                    "query": query,
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "abstract": result.summary,
                    "published": result.published.strftime("%Y-%m-%d"),
                    "updated": result.updated.strftime("%Y-%m-%d"),
                    "url": result.entry_id,
                    "pdf_url": result.pdf_url,
                    "categories": result.categories,
                    "primary_category": result.primary_category,
                })

        except Exception as e:
            logging.warning(f"ArXiv search failed for query '{query}': {str(e)}")
            continue

    # Format the results
    if not all_results:
        return "No arXiv papers found for the given queries. Try different search terms or broader topics."

    formatted_output = f"Found {len(all_results)} arXiv papers:\n\n"

    for i, paper in enumerate(all_results, 1):
        authors_str = ", ".join(paper["authors"][:3])  # Show first 3 authors
        if len(paper["authors"]) > 3:
            authors_str += f" et al. ({len(paper['authors'])} authors total)"

        formatted_output += f"--- PAPER {i}: {paper['title']} ---\n"
        formatted_output += f"Authors: {authors_str}\n"
        formatted_output += f"Published: {paper['published']} (Updated: {paper['updated']})\n"
        formatted_output += f"Category: {paper['primary_category']}\n"
        formatted_output += f"URL: {paper['url']}\n"
        formatted_output += f"PDF: {paper['pdf_url']}\n\n"
        formatted_output += f"ABSTRACT:\n{paper['abstract']}\n\n"
        formatted_output += f"SEARCH QUERY: {paper['query']}\n"
        formatted_output += "-" * 80 + "\n\n"

    return formatted_output


##########################
# ArXiv Paper Download and Read Tool
##########################

ARXIV_READ_PAPER_DESCRIPTION = (
    "Download and extract full text content from arXiv papers. "
    "Use this when you need to read the full paper content, not just the abstract. "
    "Provide the arXiv ID (e.g., '2301.07041') or full URL."
)


@tool(description=ARXIV_READ_PAPER_DESCRIPTION)
async def arxiv_read_paper(
    arxiv_ids: List[str],
    max_chars: Annotated[int, InjectedToolArg] = 50000,
    config: RunnableConfig = None
) -> str:
    """Download and extract full text from arXiv papers.

    Args:
        arxiv_ids: List of arXiv IDs or URLs (e.g., ["2301.07041", "https://arxiv.org/abs/2301.07041"])
        max_chars: Maximum characters to extract per paper (default: 50000)
        config: Runtime configuration

    Returns:
        Formatted string containing the full paper text
    """
    all_papers = []

    for arxiv_id in arxiv_ids:
        try:
            # Clean the ID (remove URL parts if present)
            if "arxiv.org" in arxiv_id:
                arxiv_id = arxiv_id.split("/")[-1]
            arxiv_id = arxiv_id.replace(".pdf", "")

            # Search for the paper to get metadata
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(search.results())

            # Download the PDF
            pdf_path = paper.download_pdf()

            # Extract text from PDF
            doc = pymupdf.open(pdf_path)
            full_text = ""

            for page in doc:
                full_text += page.get_text()

            doc.close()

            # Truncate if too long
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + f"\n\n[TRUNCATED - Original length: {len(full_text)} chars]"

            all_papers.append({
                "arxiv_id": arxiv_id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "published": paper.published.strftime("%Y-%m-%d"),
                "content": full_text,
            })

        except Exception as e:
            logging.warning(f"Failed to download/read paper {arxiv_id}: {str(e)}")
            all_papers.append({
                "arxiv_id": arxiv_id,
                "title": "ERROR",
                "authors": [],
                "published": "N/A",
                "content": f"Error reading paper: {str(e)}",
            })

    # Format output
    if not all_papers:
        return "Failed to retrieve any papers. Please check the arXiv IDs and try again."

    formatted_output = ""
    for i, paper in enumerate(all_papers, 1):
        authors_str = ", ".join(paper["authors"][:3])
        if len(paper["authors"]) > 3:
            authors_str += " et al."

        formatted_output += f"\n\n{'=' * 80}\n"
        formatted_output += f"PAPER {i}: {paper['title']}\n"
        formatted_output += f"{'=' * 80}\n"
        formatted_output += f"arXiv ID: {paper['arxiv_id']}\n"
        formatted_output += f"Authors: {authors_str}\n"
        formatted_output += f"Published: {paper['published']}\n\n"
        formatted_output += f"FULL TEXT:\n{paper['content']}\n"
        formatted_output += f"{'=' * 80}\n\n"

    return formatted_output


##########################
# Get ArXiv Tools
##########################

def get_arxiv_tools():
    """Get all arXiv research tools.

    Returns:
        List of arXiv tools for research
    """
    return [arxiv_search, arxiv_read_paper]
