# Copilot Instructions — Alter Ego

> **Before starting any plan or making changes**: Read `docs/fixes/` for known past mistakes to avoid repeating them, and `docs/plan/` for the approved improvement roadmap. Only implement items that have been explicitly approved.

A personal AI chatbot representing Aayush Vijayvergiya, deployed on Hugging Face Spaces. It answers career/background questions via a Gradio chat UI, using GPT-4o-mini with OpenAI function calling.

## Commands

```bash
uv sync                                    # Install dependencies
uv run python main.py                      # Run locally
uv run pytest tests/                       # Run full test suite
uv run pytest tests/test_alter_ego.py::TestConfig::test_config_initialization  # Single test
uv run black src/ tests/ && uv run isort src/ tests/  # Format
uv run mypy src/                           # Type check
```

All Python commands should be run via `uv run`. Never use `pip install` — this project uses `uv`.

## Architecture

```
main.py                    # Local dev entry point → imports from src.alter_ego
app.py (root)              # Hugging Face Spaces entry point (port 7860) — manually injects src/ into sys.path
src/alter_ego/
  app.py                   # AlterEgoApp class + create_app() factory
  config.py                # Singleton `config` object — all env vars and file paths
  tools.py                 # OpenAI function/tool definitions (JSON schema)
  models/__init__.py       # Python @dataclass models (UserDetails, UnknownQuestion, ToolResult, etc.)
  services/
    chat_service.py        # ChatService — orchestrates OpenAI calls + tool-call loop
    document_service.py    # DocumentService — PDF, text, and portfolio web scraping with caching
    github_service.py      # GitHubService — GitHub profile + top repos via REST API with caching
    notification_service.py# NotificationService — Pushover push notifications
    tool_handler.py        # ToolHandler — dispatches OpenAI tool calls to Python methods
static/
  AayushVijayvergiya_LinkedIn.pdf  # Loaded at startup as chatbot context
  summary.txt                      # Loaded at startup as chatbot context
  portfolio_cache.json             # Auto-generated cache for portfolio website scraping
  github_cache.json                # Auto-generated cache for GitHub API data
tests/
  test_alter_ego.py        # pytest tests using unittest.mock
```

### Data flow
1. Gradio → `AlterEgoApp.chat_handler()` → `ChatService.chat()`
2. `ChatService` builds a system prompt from `DocumentService` (PDF + text + portfolio) and `GitHubService` (profile + repos) on first call (all cached)
3. Calls OpenAI with `AVAILABLE_TOOLS`; if `finish_reason == "tool_calls"`, passes to `ToolHandler`
4. `ToolHandler` dispatches by tool name (method name must match tool name in `tools.py`)
5. Tool results (`record_user_details`, `record_unknown_question`) trigger Pushover notifications via `NotificationService`

## Key Conventions

### Two entry points, two import styles
- `main.py` (local): `from src.alter_ego import create_app` (absolute, `src/` on PYTHONPATH via package structure)
- `app.py` (HF Spaces): manually does `sys.path.insert(0, str(src_path))` then `from alter_ego import create_app`
- Inside the package: always use relative imports (`from ..config import config`, `from .services import ChatService`)

### Adding a new OpenAI tool
Two steps are always required:
1. Define the JSON schema in `tools.py` and add it to `AVAILABLE_TOOLS`
2. Add a method with the **exact same name** as the tool to `ToolHandler` — dispatch is done via `getattr(self, tool_name)`

### Config singleton
`config.py` exports a module-level `config = Config()` instance. Import it as `from ..config import config`. Never instantiate `Config()` directly in application code (tests do so to test isolation).

### Document loading is lazy and cached
`DocumentService` caches LinkedIn PDF, summary, and portfolio content in instance variables on first access. Portfolio content is also persisted to `static/portfolio_cache.json` with a TTL (default 1 hour, configurable via `PORTFOLIO_CACHE_DURATION`).

### Models use dataclasses
All data models are Python `@dataclass` (not Pydantic). They live in `src/alter_ego/models/__init__.py`.

### Path resolution
`config.py` detects Hugging Face Spaces via `os.getenv("SPACE_ID")` and sets `project_root` to `/home/user/app`; locally it resolves relative to the config file location. Always use `config.static_dir` / `config.project_root` rather than hardcoding paths.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `PUSHOVER_USER` | No | Pushover user key for notifications |
| `PUSHOVER_TOKEN` | No | Pushover API token |
| `PORTFOLIO_URL` | No | Portfolio website URL to scrape for additional context |
| `PORTFOLIO_CACHE_DURATION` | No | Cache TTL in seconds (default: 3600) |
| `GITHUB_USERNAME` | No | GitHub username to fetch repos from (default: `aayushvijayvergiya`) |
| `GITHUB_TOKEN` | No | GitHub PAT — raises rate limit from 60 to 5000 req/hr |
| `GITHUB_CACHE_DURATION` | No | GitHub data cache TTL in seconds (default: 3600) |
| `REQUEST_TIMEOUT` | No | HTTP timeout for web scraping (default: 10) |

Copy `.env.example` to `.env` for local development.

## Code Style & Standards

### Formatting & Linting
- Line length: **88** (Black)
- Import order: Black-compatible isort profile (`profile = "black"`)
- Type hints **required** on all function signatures — mypy enforces `disallow_untyped_defs = true`
- Python 3.12+
- Run before committing: `uv run black src/ tests/ && uv run isort src/ tests/ && uv run mypy src/`

### Naming Conventions (PEP 8)
- Classes: `PascalCase` (e.g., `ChatService`, `DocumentService`)
- Functions/methods: `snake_case`
- Private methods/attributes: `_single_underscore` prefix (e.g., `_build_system_prompt`, `_linkedin_content`)
- Constants / module-level singletons: `UPPER_SNAKE_CASE` for true constants (e.g., `AVAILABLE_TOOLS`), lowercase for the config singleton (`config = Config()`)
- Never use bare `l`, `O`, or `I` as single-character variable names

### Docstrings (PEP 257)
- Every module, class, and public method must have a docstring
- One-liner for simple methods; multi-line with blank line after summary for complex ones
- Private helper methods (`_`) may use one-line docstrings

### Error Handling
- Never use bare `except:` — always catch specific exception types (e.g., `except requests.RequestException`, `except json.JSONDecodeError`)
- All I/O operations (file reads, HTTP requests, PDF parsing) must have try/except with a graceful fallback — the app must never crash due to a missing file or failed network call
- Log errors with `print(f"Error description: {e}")` — do not silently swallow exceptions

### Project-Specific Rules
- **All env vars must be accessed through `config`** — never call `os.getenv()` outside of `config.py`
- **Never instantiate `Config()` in application code** — import the singleton: `from ..config import config`
- **Never hardcode file paths** — always use `config.static_dir`, `config.project_root`, etc.
- **Lazy init + instance variable caching** is the standard pattern for expensive resources (PDF, web scrapes) — see `DocumentService` as the reference implementation
- **Relative imports within the package** — use `from ..config import config`, not `from src.alter_ego.config import config`
- **One class per service file** — keep service responsibilities narrow and focused
- **validate_config() only blocks on truly fatal missing config** — optional integrations (Pushover, email, GitHub) must be handled gracefully at the service level, not at startup

### HF Deployment Rules
- `sdk_version` in `README.md` **must always match** the exact `gradio==X.Y.Z` version pinned in `requirements.txt` — mismatches cause build failures
- After any `uv lock --upgrade` or package version change: regenerate `requirements.txt` with `uv export --format requirements-txt --no-hashes --output-file requirements.txt` and update `sdk_version` accordingly
- `requirements.txt` is for HF Spaces production only — dev deps (`pytest`, `black`, etc.) go in `pyproject.toml [project.optional-dependencies] dev` only

## Docs Reference

| Directory | Contents |
|---|---|
| `docs/fixes/` | Per-date fix logs — read before starting work to avoid repeating known mistakes |
| `docs/plan/` | Dated improvement plans — only implement items with explicit approval |

New fix sessions: create `docs/fixes/YYYY-MM-DD_fixes.md`. New plans: create `docs/plan/YYYY-MM-DD.md`.
