# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run the agent (via LangGraph CLI):**
```bash
langgraph up
```

**No test or lint infrastructure is currently configured.**

## Environment Setup

Copy `.env` and populate these keys before running:
- `INCEPTION_API_KEY` — primary LLM (Inception Labs Mercury-2); falls back to OpenAI if absent
- `OPENAI_API_KEY` — fallback LLM
- `TAVILY_API_KEY` — web search/extract/crawl
- `LANGSMITH_API_KEY` — LLM observability (optional)
- `LANGGRAPH_DATABASE_URL` — PostgreSQL for persistent checkpoints (optional; defaults to in-memory)

Optional tuning vars: `MAX_SUBAGENTS_ITERATIONS` (default 3), `MAX_CONCURRENT_RESEARCH_UNITS` (default 5), `RECURSION_LIMIT` (default 50).

## Architecture

**Entry point:** `langgraph.json` maps the `research` graph to `agent.py:build_agent`.

**`agent.py`** — builds a `deepagents` multi-agent graph:
- `AgentConfig` (Pydantic): validates env-driven config
- `SubAgent` (dataclass): defines name, description, system_prompt, tools for each sub-agent
- `build_agent()`: initializes the LLM (Inception → OpenAI fallback), constructs 3 sub-agents, assembles middleware, and returns a LangGraph `Runnable`

**Three sub-agents**, each with isolated tools and prompts:
| Sub-agent | Tool(s) | Use case |
|---|---|---|
| `research-agent` | `tavily_search`, `think` | General web search |
| `extraction-agent` | `tavily_extract`, `think` | Deep extraction from known URLs |
| `crawling-agent` | `tavily_crawl`, `think` | Multi-page documentation crawling |

**Middleware stack** (applied in order):
1. `ToolRetryMiddleware` — retries up to 3×, 2× backoff, on `TimeoutError`/`ConnectionError`/`UsageLimitExceededError`
2. `SummarizationMiddleware` — summarizes context at 80% window fill
3. `FilesystemFileSearchMiddleware` — scopes file access to `./workspace`

**`tools.py`** — four LangChain tools: `tavily_search`, `tavily_extract`, `tavily_crawl`, `think_tool`. The Tavily client is lazily initialized as a module-level singleton.

**`prompts/`** — six Markdown prompt templates loaded at startup. The orchestrator prompt is assembled from `research_workflow_instructions.md` + `task_description_prefix.md` + `subagent_delegation_instructions.md`. Sub-agent prompts accept a `{date}` format argument.

**Output:** The orchestrator writes research results to `./workspace/final_report.md`.

## Known Issues

`tools.py` has bugs in `tavily_extract` and `tavily_crawl`:
- `tavily_client` is referenced but not initialized (should use `_get_tavily_client()`)
- `List` is imported from `typing_extensions` but `from typing import List` is missing
- `topic` variable used instead of `query` in `tavily_extract`
