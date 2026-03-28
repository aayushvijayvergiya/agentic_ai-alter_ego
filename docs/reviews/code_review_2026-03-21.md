# Code Review - Alter Ego (2026-03-21)

## Overview
The **Alter Ego** project is a well-engineered AI assistant designed to represent a professional profile. The codebase is modular, clean, and follows modern Python practices. It effectively integrates with external APIs (OpenAI/OpenRouter, GitHub, Pushover) and handles local document processing.

---

## High-Level Assessment

### Strengths
- **Modular Architecture:** Clear separation of concerns between UI (Gradio), Application Logic (`AlterEgoApp`), and Business Logic (Services).
- **Type Hinting:** Extensive use of Python type hints improves readability and catchable errors.
- **Robust Configuration:** Centralized configuration management using `python-dotenv` and a dedicated `Config` class.
- **Efficient Caching:** Both `DocumentService` and `GitHubService` implement disk-based caching to reduce API calls and improve latency.
- **Comprehensive Testing:** A solid test suite exists for core services and models.

### Areas for Improvement
- **Synchronous Execution:** Most network and I/O operations are synchronous, which can lead to UI blocking and slower response times.
- **Context Management:** The "Long-Context" approach (stuffing all data into the system prompt) is simple but may eventually hit token limits or increase costs/latency.
- **Error Handling:** Some services use generic `Exception` blocks.
- **Logging:** Reliance on `print` statements instead of the standard `logging` library.

---

## Detailed Findings & Recommendations

### 1. Architecture & Performance
- **Recommendation: Move to Async.**
  - **Issue:** `requests` is used for all HTTP calls. This blocks the execution thread.
  - **Fix:** Transition to `httpx` or `aiohttp` for asynchronous network requests. This is particularly important for `GitHubService` which makes multiple sequential calls.
- **Recommendation: Implement RAG (Retrieval-Augmented Generation).**
  - **Issue:** Currently, the entire LinkedIn profile, GitHub summary, and Portfolio content are injected into every prompt.
  - **Fix:** As the context grows, consider using a vector database (like ChromaDB or FAISS) to retrieve only the relevant snippets based on the user's query.

### 2. Chat Logic (`ChatService.py`)
- **Recommendation: Tool Call Safety Guard.**
  - **Issue:** The `while not done` loop for handling `tool_calls` has no exit condition other than the LLM deciding it's done.
  - **Fix:** Add a `MAX_TOOL_CALLS = 5` counter to prevent potential infinite loops or excessive API usage.
- **Recommendation: Specific Error Responses.**
  - **Issue:** The generic error message "I encountered an error..." is used for all failures.
  - **Fix:** Provide slightly more context-aware error messages or log the full stack trace for debugging.

### 3. Service Layer
- **Recommendation: Document Service Optimization.**
  - **Issue:** `_scrape_website` fetches and processes the entire page every time it's not cached.
  - **Fix:** Improve the scraping logic to focus on specific tags (e.g., `<article>`, `<section>`) and perhaps add a retry mechanism for transient network errors.
- **Recommendation: GitHub Service Parallelism.**
  - **Issue:** `_fetch_profile_content` fetches repo details and then README snippets for each repo sequentially.
  - **Fix:** If moved to async, these fetches can be done in parallel using `asyncio.gather`.

### 4. Code Quality & Standards
- **Recommendation: Standard Logging.**
  - **Issue:** `print` is used throughout the project.
  - **Fix:** Implement `logging.getLogger(__name__)`. This allows for better log management (e.g., sending logs to a file or a monitoring service in production).
- **Recommendation: Dependency Management.**
  - **Observation:** The project has both `requirements.txt` and `pyproject.toml`.
  - **Fix:** Ensure consistency. Since `uv.lock` is present, `uv` seems to be the preferred tool. It might be worth documenting this in the `README.md`.

### 5. Security
- **Assessment:** Good job keeping secrets in `.env`.
- **Note:** Ensure `.env` is never committed (it is already in `.gitignore`).

### 6. Testing
- **Recommendation: Integration Tests.**
  - **Issue:** Current tests are unit-focused.
  - **Fix:** Add integration tests for the full chat flow, mocking the OpenAI client response.
- **Recommendation: Coverage.**
  - **Observation:** `DocumentService` and `ToolHandler` lack dedicated test files (though some logic might be covered indirectly).

---

## Proposed Next Steps (Post-Approval)
1.  **Refactor Services to Async:** Start with `NotificationService` and `GitHubService`.
2.  **Implement Logging:** Replace `print` with `logging`.
3.  **Add Safety Guards:** Update `ChatService` with tool call limits.
4.  **Expand Test Suite:** Add tests for `ChatService` and `DocumentService`.

---
*Review performed by Gemini CLI.*
