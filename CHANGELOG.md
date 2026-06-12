# Changelog

## [0.1.0] - 2026-06-12

### Added
- Initial public release
- Multi-agent research pipeline with 7 agents (Supervisor, Research, Source Evaluation, Fact-Checking, Reflection, Synthesis, Report Writer)
- LangGraph-based state machine orchestration
- Multi-source search: ArXiv (with domain-specific category routing), DuckDuckGo, Wikipedia
- Two-stage relevance scoring: keyword overlap + LLM PRIMARY/SECONDARY classification
- Iterative research refinement with gap detection
- Structured markdown reports (Executive Summary, Key Findings, Analysis, Sources)
- Next.js frontend with real-time task progress
- REST API for programmatic access
- Memory persistence via Qdrant vector store
- Session management with Redis
- Docker Compose for infrastructure services
- Local LLM support via Ollama
- Multiple cloud LLM backends: Grok, Gemini, Cloudflare Workers AI
