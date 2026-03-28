# GEMINI.md — Project Governance & Standards

This document defines the core architectural principles, coding standards, and operational guidelines for the **Alter Ego** project. It takes precedence over general defaults.

## Project Vision
Alter Ego is a high-fidelity digital twin of Aayush Vijayvergiya, designed to be embedded in professional portfolios. It prioritizes low-latency (streaming), rich context (LinkedIn + GitHub + Scraped Portfolio), and proactive notifications (Email/Pushover).

## Core Architecture
- **Async-First:** All network I/O (OpenAI, GitHub API, Web Scraping, SMTP) MUST be asynchronous using `httpx` or `asyncio.to_thread`.
- **Service-Oriented:** Logic is encapsulated in specialized services (`ChatService`, `GitHubService`, `DocumentService`, `NotificationService`).
- **Two-Pass Chat:**
    1. **Pass 1 (Non-Streaming):** Handle potential tool/function calls.
    2. **Pass 2 (Streaming):** Once tools are settled, stream the final response to the UI.
- **Config Singleton:** `src/alter_ego/config.py` is the single source of truth for environment variables and paths.

## Coding Standards
- **Typing:** Strict type hinting is mandatory. Use `mypy` for validation.
- **Logging:** Use `src/alter_ego/utils/logger.py` for all output. Never use `print()`.
- **Formatting:** Adhere to `black` (line-length 88) and `isort`.
- **Testing:** All new features must include `pytest` cases with appropriate mocking of external APIs.
- **Error Handling:** Catch specific exceptions; provide graceful fallbacks (e.g., returning cached data if an API fetch fails).

## AI Safety & Constraints
- **MAX_TOOL_CALLS:** Hard limit of 5 tool calls per user turn to prevent infinite loops.
- **Rate Limiting:** Session-based message limit (default 20) to manage API costs.
- **Tool Dispatch:** `ToolHandler` must have method names exactly matching tool names defined in `tools.py`.

## Deployment (Hugging Face Spaces)
- `sdk_version` in `README.md` must strictly match the `gradio` version in `requirements.txt`.
- Use `uv export --format requirements-txt --no-hashes --output-file requirements.txt` before deployment.

---
*Last updated: 2026-03-25 by Gemini CLI.*
