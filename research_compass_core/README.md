# Research Compass Core

A streamlined research agent powered by OpenAI with ArXiv and Semantic Scholar for academic research and web search capabilities.

## Overview

Research Compass Core is a Python-based research automation system that combines academic paper search with AI-powered analysis and synthesis. Built on LangGraph, it provides a modular framework for conducting comprehensive research using OpenAI's GPT models and ArXiv's academic database.

## Key Features

### 🔍 Research Tools

1. **ArXiv Search** - Search academic papers by topic, author, or research area (no API key needed)
2. **ArXiv Read Paper** - Download and extract full text from ArXiv papers in PDF format
3. **Semantic Scholar Search** - Access 200M+ papers across all academic disciplines (optional API key for higher rate limits)
4. **Semantic Scholar Paper Details** - Get comprehensive paper information including citations and references
5. **OpenAI Native Web Search** - Built-in web search for compatible OpenAI models
6. **Strategic Think Tool** - Reflection and planning capabilities for research workflows
7. **Multi-Agent Orchestration** - Coordinate multiple research agents for complex tasks

### 🎯 Core Capabilities

- **Academic Focus**: Direct integration with ArXiv and Semantic Scholar for comprehensive academic research
- **AI-Powered Analysis**: Leverage OpenAI's GPT-4 models for synthesis and reasoning
- **Flexible Search**: Choose between ArXiv (physics/CS/math), Semantic Scholar (200M+ papers, all disciplines), web search (OpenAI), or no search
- **State Management**: Built-in conversation and research state tracking
- **Minimal Dependencies**: Streamlined codebase with only essential packages

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Setup

1. **Install the package**
   ```bash
   cd research_compass_core
   pip install -e .
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Set your API keys**
   ```bash
   # In .env file:
   OPENAI_API_KEY=your-api-key-here
   SEARCH_API=arxiv  # Options: 'arxiv', 'semantic_scholar', 'openai', 'none'

   # Optional: Semantic Scholar API key for higher rate limits (1 req/sec with key vs shared limits without)
   # Get your key at: https://www.semanticscholar.org/product/api
   SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-key  # Optional
   ```

## Usage

### Basic Research Example

```python
from research_compass_core.deep_researcher import graph
from langchain_core.messages import HumanMessage

# Configure the research session
config = {
    "configurable": {
        "thread_id": "research-session-1",
        "search_api": "arxiv",  # or "semantic_scholar" or "openai" or "none"
        "research_model": "openai:gpt-4o",
    }
}

# Execute research
result = graph.invoke(
    {
        "messages": [
            HumanMessage(content="Research the latest developments in quantum computing")
        ]
    },
    config=config
)

# Access the final report
print(result["final_report"])
```

### Configuration Options

#### Search API Selection

```python
SEARCH_API=arxiv              # ArXiv only (physics, CS, math) - default
SEARCH_API=semantic_scholar   # Semantic Scholar (200M+ papers, all disciplines)
SEARCH_API=openai             # OpenAI native web search
SEARCH_API=none               # No search functionality
```

**When to use each:**
- **ArXiv**: Best for physics, computer science, mathematics, and quantitative fields
- **Semantic Scholar**: Best for cross-disciplinary research, biology, medicine, social sciences, and comprehensive literature reviews
- **OpenAI**: Best for current events, non-academic topics, and general web information
- **None**: When using only MCP tools or custom integrations

#### Model Configuration

Customize which OpenAI models to use for different tasks:

```python
config = {
    "configurable": {
        "research_model": "openai:gpt-4o",           # Main research reasoning
        "summarization_model": "openai:gpt-4o-mini", # Paper summarization
        "compression_model": "openai:gpt-4o",        # Context compression
        "final_report_model": "openai:gpt-4o",       # Report generation
    }
}
```

### Supported OpenAI Models

- `openai:gpt-4o` - Latest GPT-4 Omni model
- `openai:gpt-4o-mini` - Faster, cost-effective variant
- `openai:gpt-4-turbo` - Previous generation GPT-4
- `openai:o1` - Reasoning-optimized models
- `openai:o3-mini` - Compact reasoning model

### Report Export

Research Compass Core can export reports to multiple formats with automatic timestamp-based versioning:

#### Available Formats

- **Markdown** (`.md`) - Default format, clean text with formatting
- **PDF** (`.pdf`) - Professional document format
- **HTML** (`.html`) - Styled web page
- **Microsoft Word** (`.docx`) - Editable document
- **JSON** (`.json`) - Structured data format
- **Plain Text** (`.txt`) - No formatting

#### Export to PDF and DOCX

```python
from research_compass_core import graph, ExportFormat

config = {
    "configurable": {
        "thread_id": "my-research",
        "search_api": "arxiv",
        "export_formats": [ExportFormat.PDF, ExportFormat.DOCX],
        "export_directory": "./research_reports"  # Optional, defaults to ./research_reports
    }
}

result = await graph.ainvoke(
    {"messages": [HumanMessage(content="Research quantum computing")]},
    config=config
)

# Access the report (always available as markdown)
print(result["final_report"])

# Access exported file paths
print(result["exported_files"])
# {'pdf': './research_reports/research_quantum_computing_20240115_143022.pdf',
#  'docx': './research_reports/research_quantum_computing_20240115_143022.docx'}
```

#### File Naming & Versioning

Files are automatically named using timestamps to prevent overwrites:

**Format**: `{sanitized_topic}_{timestamp}.{extension}`

**Example**: `quantum_computing_20240115_143022.pdf`

- Topic is sanitized from research brief (lowercase, max 50 chars)
- Timestamp format: `YYYYMMDD_HHMMSS`
- Each research run creates unique files
- No manual version management needed

#### Default Behavior

If `export_formats` is not specified, reports are only returned in memory (no files created):

```python
config = {
    "configurable": {
        "search_api": "arxiv"
        # No export_formats specified
    }
}

result = await graph.ainvoke(...)
print(result["final_report"])  # Available
print(result["exported_files"])  # Empty dict
```

## Architecture

### Project Structure

```
research_compass_core/
├── src/
│   └── research_compass_core/
│       ├── __init__.py
│       ├── configuration.py           # Environment and runtime config
│       ├── state.py                   # State definitions for agents
│       ├── prompts.py                 # System prompts and templates
│       ├── utils.py                   # Utility functions
│       ├── arxiv_tools.py             # ArXiv search & PDF tools
│       ├── semantic_scholar_tools.py  # Semantic Scholar search tools
│       ├── exporters.py               # Multi-format report export
│       └── deep_researcher.py         # Main agent graph implementation
├── pyproject.toml                     # Package dependencies
├── .env.example                       # Environment template
└── README.md                          # Documentation
```

### Agent Workflow

The research agent follows a structured workflow:

1. **Query Analysis** - Understand the research question
2. **Search Planning** - Determine search strategy (ArXiv, web, or none)
3. **Information Gathering** - Execute searches and retrieve papers/content
4. **Analysis & Synthesis** - Process findings using AI models
5. **Report Generation** - Compile comprehensive research report

### State Management

Research sessions maintain state including:
- Conversation history
- Retrieved documents and papers
- Intermediate findings
- Configuration settings
- Thread-based session tracking

## Dependencies

### Core Framework
- `langgraph` - Agent orchestration and state management
- `langchain-openai` - OpenAI model integration
- `langchain-community` - Community tool integrations
- `openai` - OpenAI Python SDK

### Research Tools
- `arxiv` - ArXiv API client for academic papers
- `pymupdf` - PDF text extraction and parsing

### Export Tools
- `markdown` - Markdown to HTML conversion
- `weasyprint` - HTML to PDF generation (no external dependencies)
- `python-docx` - Microsoft Word document creation

### Utilities
- `python-dotenv` - Environment variable management
- `httpx` - Async HTTP client
- `rich` - Terminal output formatting
- `langsmith` - Optional tracing and debugging

Total: ~16 core packages

## Advanced Usage

### Custom Agent Configuration

```python
from research_compass_core.configuration import Configuration
from research_compass_core.deep_researcher import graph

# Create custom configuration
config = Configuration(
    search_api="arxiv",
    research_model="openai:gpt-4o",
    max_search_results=10,
    enable_reflection=True
)

# Use in research
result = graph.invoke(
    {"messages": [HumanMessage(content="Your research query")]},
    config={"configurable": config.to_dict()}
)
```

### Accessing Research Artifacts

```python
# After research completion
result = graph.invoke(...)

# Access different outputs
final_report = result["final_report"]              # Markdown report
exported_files = result.get("exported_files", {})  # File paths (if export enabled)
retrieved_papers = result.get("documents", [])     # Research papers
research_history = result["messages"]              # Conversation history
```

## Environment Variables

Create a `.env` file with the following:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
SEARCH_API=arxiv                          # Search provider (arxiv, semantic_scholar, openai, none)
SEMANTIC_SCHOLAR_API_KEY=your-s2-api-key  # Optional, for higher rate limits
LANGSMITH_API_KEY=                        # For debugging/tracing
LANGSMITH_TRACING=false                   # Enable LangSmith tracing
```

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Verify your API key is valid and has credits
2. **ArXiv Timeouts**: ArXiv may rate-limit; reduce concurrent requests
3. **PDF Extraction Failures**: Some ArXiv papers have restricted access or malformed PDFs
4. **Model Not Found**: Ensure you're using valid OpenAI model identifiers

### Debug Mode

Enable LangSmith tracing for detailed agent execution logs:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
```

## Examples

### Example 1: Academic Literature Review

```python
query = """
Conduct a literature review on transformer architectures in NLP,
focusing on papers from 2020-2024. Include key innovations and benchmarks.
"""

result = graph.invoke(
    {"messages": [HumanMessage(content=query)]},
    config={"configurable": {"search_api": "arxiv"}}
)
```

### Example 2: Biomedical Research with Semantic Scholar

```python
# Use Semantic Scholar for comprehensive cross-disciplinary coverage
config = {
    "configurable": {
        "search_api": "semantic_scholar",
        "research_model": "openai:gpt-4o"
    }
}

query = """
Research the latest developments in CRISPR gene editing for cancer therapy,
focusing on clinical trials and safety considerations from 2022-2024.
"""

result = graph.invoke(
    {"messages": [HumanMessage(content=query)]},
    config=config
)
```

### Example 3: Hybrid Research (Academic + Web)

```python
# Use OpenAI web search for broader context
config = {
    "configurable": {
        "search_api": "openai",
        "research_model": "openai:gpt-4o"
    }
}

result = graph.invoke(
    {"messages": [HumanMessage(content="Latest trends in edge AI deployment")]},
    config=config
)
```

## Contributing

Contributions are welcome! Key areas for improvement:
- Additional academic databases (PubMed, IEEE, Google Scholar, etc.)
- Enhanced PDF parsing and full-text extraction for Semantic Scholar papers
- Better citation management (BibTeX export, Zotero integration)
- More export formats and customization options

## License

MIT License

## Support

For issues, questions, or feature requests, please open an issue in the repository.
