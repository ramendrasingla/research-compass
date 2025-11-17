"""Research Compass Core - Streamlined research agent using OpenAI and ArXiv."""

# Startup verification
print("🚀 Loading Research Compass Core with SOURCE EXTRACTION DEBUG v2.0")

from research_compass_core.configuration import Configuration, ExportFormat, SearchAPI
from research_compass_core.deep_researcher import deep_researcher as graph
from research_compass_core.state import (
    AgentInputState,
    AgentState,
    ClarifyWithUser,
    ConductResearch,
    ResearchComplete,
    ResearchQuestion,
    ResearcherOutputState,
    ResearcherState,
    SupervisorState,
    Summary,
)

__version__ = "1.0.0"

__all__ = [
    "Configuration",
    "ExportFormat",
    "SearchAPI",
    "graph",
    "deep_researcher",
    "AgentInputState",
    "AgentState",
    "ClarifyWithUser",
    "ConductResearch",
    "ResearchComplete",
    "ResearchQuestion",
    "ResearcherOutputState",
    "ResearcherState",
    "SupervisorState",
    "Summary",
]

# Alias for compatibility
deep_researcher = graph
