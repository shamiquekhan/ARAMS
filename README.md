# ARAMS — Autonomous Research and Multi-Agent System

An intelligent research assistant that decomposes complex queries into subtasks, searches multiple sources (ArXiv, DuckDuckGo, Wikipedia), evaluates relevance, verifies facts, and generates structured research reports — all orchestrated by a graph-based multi-agent pipeline.

## Features

- **Multi-agent orchestration** — Supervisor, Research, Source Evaluation, Fact-Checking, Synthesis, and Report Writing agents collaborate via a LangGraph state machine.
- **Intelligent query decomposition** — Breaks broad questions into focused subtasks using LLM-driven planning.
- **Multi-source search** — Queries ArXiv (with domain-specific category routing), DuckDuckGo, and Wikipedia in parallel.
- **Relevance scoring** — Two-stage filter: fast keyword overlap followed by LLM-based PRIMARY/SECONDARY/NO classification.
- **Fact verification** — Cross-references claims against source URLs and detects contradictions.
- **Iterative refinement** — Identifies knowledge gaps and re-searches with generated sub-questions until confidence threshold is met or iteration limit is reached.
- **Structured reports** — Generates Executive Summary, Key Findings, Analysis, and Sources sections with citation tracing.
- **Memory persistence** — Short-term session memory and long-term Qdrant vector store for cross-session context.
- **Dual UI** — Next.js frontend with real-time progress streaming and REST API for headless integration.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, LangGraph, LangChain |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Search | DuckDuckGo, ArXiv API, Wikipedia API |
| LLM | Ollama (local), Grok, Gemini, Cloudflare Workers AI |
| Vector Store | Qdrant |
| Database | PostgreSQL (asyncpg), Redis |
| Task Queue | Celery |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |

## Architecture

```
User Query
    │
    ▼
┌────────────────┐
│  Supervisor    │  Decomposes query into subtasks
│  Agent         │  Retrieves session memory
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Research      │  Searches ArXiv, DuckDuckGo, Wikipedia
│  Agent         │  Staggered subtask execution (1.5s gap)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Source Eval   │  Keyword overlap + LLM PRIMARY/SECONDARY/NO
│  Agent         │  Filters irrelevant sources (< 0.3 score)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Fact Checker  │  Verifies claims against source URLs
│  Agent         │  Flags contradictions
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Reflection    │  Identifies gaps, computes confidence
│  Agent         │  Decides continue vs synthesize
└───────┬────────┘
   │          │
   ▼          ▼
(loop)    ┌────────────────┐
          │  Synthesis     │  Condenses findings into insights
          │  Agent         │
          └───────┬────────┘
                  │
                  ▼
          ┌────────────────┐
          │  Report Writer │  Generates structured markdown report
          │  Agent         │  Executive Summary → Key Findings → Analysis → Sources
          └───────┬────────┘
                  │
                  ▼
          ┌────────────────┐
          │  Human Review  │  Optional approval step (auto-approve after 15s)
          └───────┬────────┘
                  │
                  ▼
          ┌────────────────┐
          │  Memory Save   │  Persists findings to Qdrant
          └────────────────┘
```

## Project Structure

```
amars/
├── backend/
│   ├── app/
│   │   ├── agents/           # Multi-agent system (7 agents)
│   │   ├── api/routes/       # FastAPI endpoints
│   │   ├── core/             # Config, LLM routing, security
│   │   ├── graph/            # LangGraph state machine
│   │   ├── memory/           # Episodic, short-term, long-term memory
│   │   ├── models/           # Pydantic schemas, ORM models
│   │   ├── rag/              # Chunking, retrieval
│   │   ├── search/           # Search tool implementations
│   │   ├── tasks/            # Celery + pipeline orchestration
│   │   └── verification/     # Hallucination detection
│   ├── tests/
│   ├── main.py               # FastAPI entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages (research, history)
│   │   ├── components/       # UI components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # API client
│   │   ├── stores/           # State management
│   │   └── types/            # TypeScript definitions
│   └── package.json
├── k8s/                      # Kubernetes manifests (WIP)
├── monitoring/               # Monitoring configs (WIP)
├── docker-compose.yml        # Multi-service Docker setup
└── .env.example              # Environment variable template
```

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (for services)
- Ollama (optional, for local LLM)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/shamiquekhan/ARAMS.git
cd ARAMS

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure services
docker-compose up -d postgres redis qdrant ollama

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend setup (in a new terminal)
cd frontend
npm install
npm run build
npm start
```

### Manual Service Setup

```bash
# PostgreSQL
docker run -d --name amars-pg -e POSTGRES_PASSWORD=amars -p 5432:5432 postgres:16

# Redis
docker run -d --name amars-redis -p 6379:6379 redis:7-alpine

# Qdrant
docker run -d --name amars-qdrant -p 6333:6333 qdrant/qdrant

# Ollama (for local LLM)
docker run -d --name amars-ollama -p 11434:11434 ollama/ollama
docker exec amars-ollama ollama pull llama3.2:1b
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Application secret key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `QDRANT_URL` | Yes | Qdrant vector store URL |
| `LLM_BACKEND` | Yes | LLM provider: `ollama`, `gemini`, `grok`, `cf` |
| `LLM_MODEL` | No | Model name (default: `llama3.2:1b`) |
| `OLLAMA_BASE_URL` | No | Ollama server URL |
| `GROK_API_KEY` | No | Grok API key |
| `GEMINI_API_KEY` | No | Gemini API key |
| `CLOUDFLARE_API_TOKEN` | No | Cloudflare Workers AI token |
| `OPENAI_API_KEY` | No | OpenAI-compatible API key |
| `TAVILY_API_KEY` | No | Tavily search API key |
| `FIRECRAWL_API_KEY` | No | Firecrawl API key |
| `MAX_RESEARCH_ITERATIONS` | No | Max research loops (default: 3) |
| `CONFIDENCE_THRESHOLD` | No | Auto-approve threshold (default: 0.85) |

## Usage

### API

```bash
# Submit a research task
curl -X POST http://localhost:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"query": "use of transformers in machine learning"}'

# Check task status
curl http://localhost:8000/api/v1/research/<task_id>

# List research history
curl http://localhost:8000/api/v1/history

# Get full report
curl http://localhost:8000/api/v1/reports/<task_id>
```

### Frontend

Open `http://localhost:3000` in your browser. Submit a query from the home page and monitor progress through the research pipeline.

## Development

```bash
# Backend (hot reload)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (hot reload)
cd frontend
npm run dev

# Run tests
cd backend && python -m pytest

# Lint
cd frontend && npm run lint
```

## Deployment

### Docker Compose

```bash
# Full stack
docker-compose up -d --build

# Scale workers
docker-compose up -d --scale worker=3
```

### Kubernetes

See `k8s/` directory for manifests (work in progress).

## Security

- API keys are stored in `.env` files and never committed to version control.
- The `.env.example` file provides placeholder templates.
- All LLM API keys support multiple providers for resilience.
- Source URLs are validated to prevent SSRF attacks.
- See `SECURITY.md` for the full security policy.

## Contributing

Contributions are welcome. See `CONTRIBUTING.md` for guidelines.

## License

MIT — see `LICENSE` for details.
