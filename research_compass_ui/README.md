# Research Compass UI

Modern web interface for Research Compass - an AI-powered research assistant that searches academic papers, synthesizes findings, and generates comprehensive research reports.

## Features

- **Clean, Modern Interface** - SciSpace-inspired design with intuitive navigation
- **Multi-Source Search** - Search across ArXiv, Semantic Scholar, and web sources
- **Real-time Progress** - Live updates via WebSocket streaming
- **AI-Powered Analysis** - Advanced AI agents synthesize research findings
- **Multiple Export Formats** - Export to PDF, DOCX, HTML, Markdown, JSON, and TXT
- **Research History** - Track and manage past research sessions
- **Advanced Configuration** - Customize models, iterations, and search APIs

## Architecture

### Tech Stack

**Frontend:**
- React 18 with TypeScript
- Tailwind CSS for styling
- React Router for navigation
- React Markdown for report rendering
- Lucide React for icons
- Vite for build tooling

**Backend:**
- FastAPI (Python)
- WebSocket for real-time streaming
- Integration with `research_compass_core`

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- npm or yarn
- OpenAI API key
- (Optional) Semantic Scholar API key

## Installation

### 1. Install the Python package

First, ensure you have `research_compass_core` installed:

```bash
# From the research-compass root directory
cd research_compass_core
pip install -e .
```

### 2. Install the UI package

```bash
cd ../research_compass_ui
pip install -e .
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Set up environment variables

Create a `.env` file in the `research_compass_ui` directory:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=research-compass
LANGSMITH_TRACING=false
```

## Running the Application

### Development Mode

You need to run both the backend and frontend:

**Terminal 1 - Backend:**
```bash
cd research_compass_ui/backend
python -m app.main
```

The backend will start on `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd research_compass_ui/frontend
npm run dev
```

The frontend will start on `http://localhost:3000`

### Production Mode

**Build the frontend:**
```bash
cd frontend
npm run build
```

**Run the backend:**
```bash
cd ../backend
python -m app.main
```

The built frontend will be served by the backend at `http://localhost:8000`

## Usage

1. **Start Research**
   - Go to the home page
   - Enter your research question
   - (Optional) Click "Advanced Options" to customize settings
   - Click "Start Research"

2. **Monitor Progress**
   - View real-time updates in the progress panel
   - Watch as the AI agents search and synthesize information
   - See the final report as it's generated

3. **View Results**
   - Read the comprehensive research report
   - Download in your preferred format
   - Access exported files

4. **Manage History**
   - View all past research sessions
   - Resume or review previous research
   - Delete old sessions

## Configuration Options

### Search APIs

- **ArXiv** - Academic papers in CS, physics, mathematics
- **Semantic Scholar** - 200M+ papers across all disciplines
- **OpenAI Web Search** - General web search
- **None** - Standalone mode for custom tools

### Models

- **gpt-4o** - Latest GPT-4 Omni (best quality)
- **gpt-4o-mini** - Faster, cost-effective
- **gpt-4-turbo** - Previous generation
- **o1** / **o3-mini** - Reasoning-optimized

### Export Formats

- Markdown (`.md`)
- PDF (`.pdf`)
- HTML (`.html`)
- Word Document (`.docx`)
- JSON (`.json`)
- Plain Text (`.txt`)

## API Endpoints

### REST Endpoints

- `GET /api/health` - Health check
- `POST /api/research/start` - Start new research session
- `GET /api/research/sessions` - List all sessions
- `GET /api/research/session/{id}` - Get session details
- `DELETE /api/research/session/{id}` - Delete session
- `GET /api/config/models` - Get available models
- `GET /api/config/search-apis` - Get available search APIs
- `GET /api/config/export-formats` - Get export formats

### WebSocket

- `WS /api/research/stream/{id}` - Stream research progress

## Project Structure

```
research_compass_ui/
├── backend/                    # Backend API
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── config.py      # Configuration endpoints
│   │   │   ├── research.py    # Research endpoints + WebSocket
│   │   │   └── sessions.py    # Session management
│   │   ├── core/              # Core utilities
│   │   │   └── config.py      # Application settings
│   │   ├── models/            # Pydantic models
│   │   │   └── schemas.py     # Request/response schemas
│   │   ├── services/          # Business logic
│   │   │   └── research_service.py
│   │   ├── storage/           # Data storage
│   │   │   └── session_store.py
│   │   └── main.py            # FastAPI application
│   ├── pyproject.toml
│   └── README.md
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   └── Layout.tsx
│   │   ├── pages/            # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── ResearchPage.tsx
│   │   │   └── HistoryPage.tsx
│   │   ├── services/         # API client
│   │   │   └── api.ts
│   │   ├── types/            # TypeScript types
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── .env                       # Environment variables
├── run.sh                     # Development runner
└── README.md
```

## Troubleshooting

### Backend won't start

- Ensure `research_compass_core` is installed: `pip install -e ../research_compass_core`
- Check that your `.env` file has the required `OPENAI_API_KEY`
- Verify Python version: `python --version` (should be 3.10+)

### Frontend won't start

- Install dependencies: `cd frontend && npm install`
- Check Node version: `node --version` (should be 18+)
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

### WebSocket connection fails

- Ensure backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Verify the WebSocket URL in `frontend/src/utils/api.ts`

### Research fails to start

- Check OpenAI API key is valid
- Verify you have sufficient API credits
- Check backend logs for error messages

## Development

### Adding new features

1. **Backend changes**: Edit files in `backend/app/`
   - API routes: `backend/app/api/`
   - Business logic: `backend/app/services/`
   - Data models: `backend/app/models/schemas.py`
2. **Frontend changes**: Edit files in `frontend/src/`
3. **Styling**: Use Tailwind CSS classes in components

### Running tests

```bash
# Backend tests
pytest

# Frontend tests (if configured)
cd frontend
npm test
```

### Linting

```bash
# Backend
cd backend
ruff check app/

# Frontend
cd frontend
npm run lint
```

## License

MIT

## Credits

Built with:
- [Research Compass Core](../research_compass_core)
- [LangChain](https://langchain.com)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [OpenAI](https://openai.com)
- [FastAPI](https://fastapi.tiangolo.com)
- [React](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
