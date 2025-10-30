# Quick Start Guide

Get Research Compass UI up and running in 5 minutes.

## Prerequisites Check

```bash
# Check Python version (need 3.10+)
python --version

# Check Node.js version (need 18+)
node --version

# Check npm
npm --version
```

## Step-by-Step Setup

### 1. Install Research Compass Core

```bash
# From research-compass root directory
cd research_compass_core
pip install -e .
```

### 2. Install UI Dependencies

```bash
# Install Python backend
cd ../research_compass_ui/backend
pip install -e .

# Install frontend dependencies
cd ../frontend
npm install
cd ..
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

Required in `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

### 4. Run the Application

#### Option A: Using the run script (Recommended)

```bash
chmod +x run.sh
./run.sh
```

#### Option B: Manual start

**Terminal 1 - Backend:**
```bash
cd backend
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access the Application

Open your browser to: **http://localhost:3000**

## Your First Research

1. Enter a research question in the search box
   Example: "What are the latest advances in quantum computing?"

2. (Optional) Click "Advanced Options" to customize:
   - Search API (ArXiv, Semantic Scholar, etc.)
   - AI models
   - Export formats

3. Click "Start Research"

4. Watch the AI agents work in real-time:
   - Search academic papers
   - Analyze findings
   - Generate comprehensive report

5. View and download your research report!

## Common Issues

### "research_compass_core not found"
```bash
cd ../research_compass_core
pip install -e .
```

### "OPENAI_API_KEY not set"
Edit `.env` file and add your OpenAI API key.

### Port already in use
If port 8000 or 3000 is in use, you can change them:
- Backend: Edit `backend/app/core/config.py`, change `port = 8000`
- Frontend: Edit `frontend/vite.config.ts`, change `port: 3000`

### Frontend shows connection error
Ensure the backend is running on port 8000:
```bash
curl http://localhost:8000/api/health
```

## Next Steps

- Check out [README.md](README.md) for detailed documentation
- Explore the [History](http://localhost:3000/history) page to see past research
- Try different search APIs and models
- Export reports in multiple formats

## Getting Help

- Backend logs: Check the terminal running the backend server
- Frontend logs: Open browser DevTools (F12) → Console
- API docs: http://localhost:8000/docs (FastAPI Swagger UI)

## Stopping the Application

- If using `run.sh`: Press `Ctrl+C`
- If running manually: Press `Ctrl+C` in both terminals

---

Happy researching! 🧭
