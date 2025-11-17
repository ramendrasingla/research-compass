"""Diagram specification tools for research reports.

This module provides tools for the research supervisor to specify where and what type
of diagrams should be included in the final report to enhance visual understanding.
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal, List


class DiagramSpecification(BaseModel):
    """Specification for a diagram to be included in the report."""

    section: str = Field(
        description="Section name or heading where diagram should appear"
    )
    diagram_type: Literal["flowchart", "mindmap", "sequence", "timeline", "hierarchy"] = Field(
        description="Type of mermaid diagram to generate"
    )
    title: str = Field(
        description="Title/caption for the diagram"
    )
    description: str = Field(
        description="Detailed description of what the diagram should show, including nodes, relationships, and flow"
    )
    concepts: List[str] = Field(
        description="Key concepts/nodes to include in the diagram"
    )


@tool
def specify_diagram(
    section: str,
    diagram_type: str,
    title: str,
    description: str,
    concepts: List[str]
) -> str:
    """Specify where and what type of diagram should be included in the final report.

    Use this tool when analyzing research findings to identify where a visual diagram
    would significantly enhance understanding of complex relationships, processes, or hierarchies.

    This tool is for the research supervisor to strategically plan diagram placement.

    Args:
        section: The section/heading where this diagram belongs (e.g., "2. Neural Network Architecture")
        diagram_type: Type of diagram - flowchart (processes/decisions), mindmap (concept relationships),
                      sequence (interactions), timeline (chronological), hierarchy (organizational structure)
        title: Caption for the diagram (e.g., "Information Flow in Transformer Model")
        description: Detailed description of the diagram content and structure - be very specific about
                    what nodes should be included and how they connect
        concepts: List of key concepts/nodes to include in the diagram

    Returns:
        Confirmation message that the diagram has been specified

    Example:
        specify_diagram(
            section="2. Transformer Architecture",
            diagram_type="flowchart",
            title="Information Flow in Transformer Model",
            description="Show how input tokens flow through embedding layer, then positional encoding, "
                       "through multi-head attention mechanism, into feed-forward network, and finally to output layer",
            concepts=["Input Tokens", "Embedding", "Positional Encoding", "Multi-Head Attention", "Feed Forward", "Output"]
        )
    """
    spec = DiagramSpecification(
        section=section,
        diagram_type=diagram_type,
        title=title,
        description=description,
        concepts=concepts
    )

    return f"Diagram specified for section '{section}': {diagram_type} titled '{title}' with {len(concepts)} key concepts."
