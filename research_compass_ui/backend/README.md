# Research Compass UI - Backend

This is the backend API for Research Compass UI, built with FastAPI.

## Directory Structure

```
backend/
├── app/                      # Application code
│   ├── api/                  # API route handlers
│   │   ├── config.py         # Configuration endpoints
│   │   ├── research.py       # Research endpoints + WebSocket
│   │   └── sessions.py       # Session management endpoints
│   ├── core/                 # Core utilities
│   │   └── config.py         # Application settings
│   ├── models/               # Pydantic models
│   │   └── schemas.py        # Request/response schemas
│   ├── services/             # Business logic
│   │   └── research_service.py  # Research operations
│   ├── storage/              # Data storage
│   │   └── session_store.py  # In-memory session storage
│   └── main.py               # FastAPI application
├── pyproject.toml            # Dependencies and config
└── README.md                 # This file
```

## Requirements

- Python 3.10+
- `research_compass_core` package installed

## Installation

From the `backend/` directory:

```bash
pip install -e .
```

Or install dependencies only:

```bash
pip install fastapi uvicorn[standard] python-multipart python-dotenv pydantic pydantic-settings aiofiles research_compass_core
```

## Running the Server

### Development Mode

From the `backend/` directory:

```bash
python -m app.main
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### From Project Root

```bash
cd backend
python -m app.main
```

## Configuration

Create a `.env` file in the project root (one level up from `backend/`) with:

```bash
OPENAI_API_KEY=your_key_here
SEMANTIC_SCHOLAR_API_KEY=your_key_here  # Optional
LANGSMITH_API_KEY=your_key_here         # Optional
LANGSMITH_PROJECT=research-compass
LANGSMITH_TRACING=false
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /api/health` - Health check

### Research
- `POST /api/research/start` - Start new research session
- `WebSocket /api/research/stream/{session_id}` - Stream research progress

### Sessions
- `GET /api/research/sessions` - List all sessions
- `GET /api/research/session/{session_id}` - Get session details
- `DELETE /api/research/session/{session_id}` - Delete session

### Configuration
- `GET /api/config/models` - List available models
- `GET /api/config/search-apis` - List available search APIs
- `GET /api/config/export-formats` - List available export formats

## Development

### Code Style

This project uses Ruff for linting and formatting:

```bash
pip install ruff
ruff check app/
ruff format app/
```

### Testing

```bash
pip install pytest pytest-asyncio
pytest
```
