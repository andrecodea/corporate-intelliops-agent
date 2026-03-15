# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run integration test:**
```bash
python tests/run_agent.py "your query here"
```

**Run the agent (via LangGraph CLI):**
```bash
langgraph up
```

## Environment Setup

Copy `.env` and populate these keys before running:
- `ANTHROPIC_API_KEY` — primary LLM (claude-sonnet-4-6 by default); falls back to OpenAI if absent
- `OPENAI_API_KEY` — fallback LLM (gpt-5.2 by default)
- `TAVILY_API_KEY` — web search/crawl
- `LANGSMITH_API_KEY` — LLM observability (optional)
- `LANGGRAPH_DATABASE_URL` — PostgreSQL for persistent checkpoints (optional; defaults to in-memory)

Optional tuning vars: `MAX_SUBAGENTS_ITERATIONS` (default 3), `MAX_CONCURRENT_RESEARCH_UNITS` (default 5), `RECURSION_LIMIT` (default 50), `MODEL_NAME`, `BASE_URL`, `FALLBACK_MODEL`, `SUMMARIZER_MODEL`.

## Architecture

**Entry point:** `langgraph.json` maps the `research` graph to `agent.py:build_agent`.

**`agent.py`** — builds a `deepagents` multi-agent graph:
- `LLMConfig` / `AgentConfig` (Pydantic): validate env-driven config
- `SubAgent` (dataclass): defines name, description, system_prompt, tools for each sub-agent
- `build_agent()`: initializes the LLM (Inception → OpenAI fallback), constructs 2 sub-agents, assembles middleware, returns a LangGraph `Runnable`
- Uses `FilesystemBackend(root_dir=workspace/, virtual_mode=True)` so agents write files with virtual paths (`/research_request.md` → `workspace/research_request.md`)

**Two sub-agents**, each with isolated tools and prompts:
| Sub-agent | Tool(s) | Use case |
|---|---|---|
| `research-agent` | `tavily_search`, `tavily_extract` | Web search + inline extraction when snippets are insufficient |
| `crawling-agent` | `tavily_crawl` | Multi-page documentation crawling |

**Middleware stack** (orchestrator, applied after deepagents defaults):
1. `ToolRetryMiddleware` — retries up to 3×, 2× backoff, on `TimeoutError`/`ConnectionError`/`UsageLimitExceededError`
2. `SummarizationMiddleware` — compresses context at 10k tokens, keeps 50%

Sub-agents also receive a `SummarizationMiddleware(trigger=("tokens", 8000), keep=0.5)` injected via the `middleware` key in their spec.

**`tools.py`** — four LangChain tools: `tavily_search`, `tavily_extract`, `tavily_crawl`, `think_tool`. The Tavily client is lazily initialized as a module-level singleton. `max_results` in `tavily_search` is `InjectedToolArg` (hidden from LLM, fixed at 1).

**`prompts/`** — five Markdown prompt templates loaded at startup:
- Orchestrator: `orchestrator_agent_instructions.md` + `task_description_prefix.md` + `subagent_delegation_instructions.md`
- Sub-agents: `research_agent_instructions.md`, `crawling_agent_instructions.md`
- Sub-agent prompts accept a `{date}` format argument

**`workspace/`** — runtime output directory. `report_guidelines.md` lives here (loaded lazily by the agent when writing the final report). Agent-generated files (`research_request.md`, `final_report.md`) are excluded from git.

**`tests/run_agent.py`** — manual integration test. Measures TTFT, latency, and per-call token usage. Saves runs to `tests/runs/`. Cleans workspace before each run.

## Known Limitations

- **mercury-2 (Inception Labs)** does not reliably follow hard iteration limits in prompts, causing sub-agents to run more tool calls than instructed. This leads to high cumulative token usage and rate limit errors on lower API tiers.
- Sub-agent internal iteration count has no hard code-level cap in deepagents (only prompt-based limits). `max_subagent_iterations` and `max_concurrent_research_units` in `AgentConfig` are prompt-only — they are not enforced by the framework.
