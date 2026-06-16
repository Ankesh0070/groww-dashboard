# Edge Cases and Failure Modes

This document outlines the corner cases and potential failure modes for the **Groww Weekly Product Review Pulse** system, categorized by the architectural tiers.

---

## 1. Ingestion (Play Store MCP Server)

| Edge Case | Impact | Current Mitigation / Needed Action |
| :--- | :--- | :--- |
| **No reviews in the timeframe** | Pipeline has no data to process. | The Orchestrator checks `if not raw_reviews:` and exits gracefully. |
| **Scraper Rate Limiting / Blocking** | `google-play-scraper` fails due to IP blocks. | The MCP server wraps the call in a `try/catch` and returns an error message. *Future:* Add retry logic with exponential backoff or use residential proxies. |
| **Non-English Reviews** | Feedback is in Hindi or regional languages. | Gemini 1.5 natively handles multi-lingual clustering. Verbatim quotes will be extracted in the original language. |
| **Extremely High Review Volume** | App receives 10,000+ reviews in a week, slowing down pagination or causing memory issues. | Pagination in `index.js` is currently capped at 15 pages (1500 reviews max) to prevent memory bloat and keep payload sizes reasonable. |

## 2. Core Processing Engine

| Edge Case | Impact | Current Mitigation / Needed Action |
| :--- | :--- | :--- |
| **PII Scrubber False Positives** | Normal text is incorrectly redacted (e.g., the word "reference" matching an ID pattern). | Modified `ID_REGEX` to strictly require at least one digit in the identifier value. |
| **LLM Context Window Exceeded** | Too many reviews exceed the LLM's token limit. | Gemini 1.5 Flash has a 1-million token window, making this highly unlikely for 1500 reviews. *Future:* Chunking or sampling if we switch models. |
| **LLM JSON Schema Violation** | The LLM returns malformed JSON or plain text instead of the requested schema. | `processor.py` has a robust fallback parser that strips markdown ticks (` ```json `). If it still fails, it raises a `ValueError` to prevent garbage data from being published. |
| **LLM Quote Hallucination** | LLM paraphrases a quote or fixes a typo, breaking the verbatim requirement. | `validator.py` standardizes text (lowercasing, stripping punctuation) and does a substring check. If it fails, the quote is dropped entirely before the report is generated. |

## 3. Workspace Delivery & Idempotency

| Edge Case | Impact | Current Mitigation / Needed Action |
| :--- | :--- | :--- |
| **Partial Delivery Failure** | Google Docs append succeeds, but Gmail draft creation fails. | The CLI logs the partial success locally. *Future:* Implement a retry queue for failed delivery steps. |
| **Concurrency / Race Condition** | The CLI is triggered twice simultaneously for the same week. | `is_week_processed` checks the JSON log. *Note:* Local file locking is not currently implemented. Assume sequential cron execution. |
| **Google Doc Size Limits** | After several years of weekly appends, the single Google Doc becomes too large or slow to open. | *Future:* Implement a rolling mechanism to create a new "Yearly" document every January. |
| **Missing API Keys** | `GEMINI_API_KEY` is not set in the environment. | Dry-runs fall back to a local "mock analysis mode" to allow pipeline testing. Live runs will abort cleanly with an error message. |
| **Invalid Doc ID or Missing Permissions** | The Google Docs MCP fails to write to the specified Document. | The MCP call throws an error. The CLI catches the exception and outputs the markdown locally for verification so data isn't lost. |
