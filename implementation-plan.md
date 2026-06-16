# Implementation Plan — Weekly Product Review Pulse (Groww)

This plan outlines the phase-wise implementation of the automated weekly pulse system for **Groww** Google Play Store reviews, using Model Context Protocol (MCP) servers for review ingestion and Google Workspace delivery.

---

## User Review Required

> [!IMPORTANT]
> - **Google Workspace MCP Credentials**: Please ensure the standard Google Docs and Gmail MCP servers are installed and authorized on your client.
> - **LLM Selection**: We will be using the **Groq API** with the `llama-3.3-70b-versatile` model. Ensure your local environment has `GROQ_API_KEY` configured.

---

## Proposed Changes & Phased Checklist

### Phase 1: Custom Play Store Reviews MCP Server
Build and expose the custom local MCP server to retrieve public reviews for Groww.

#### [NEW] [mcp-server-playstore/](file:///c:/Projects/Groww/mcp-server-playstore)
- Create a Node.js or Python project implementing the Model Context Protocol.
- Implement the `fetch_play_store_reviews` tool using `google-play-scraper`.
- Expose parameters for filtering reviews by date range / rolling week count (default 8-12 weeks).
- Verify the server locally using the MCP inspector.

---

### Phase 2a: Preprocessing & Local Clustering (Hinglish Support)
Due to strict LLM token limits, we cannot pass all reviews into an LLM context natively. We must handle clustering locally.

#### [NEW] [src/core/scrubber.py](file:///c:/Projects/Groww/src/core/scrubber.py)
- Regex-based and entity-based PII scrubber (cleans emails, phone numbers, customer IDs, and personal names).

#### [MODIFY] [src/core/processor.py](file:///c:/Projects/Groww/src/core/processor.py)
- **Score-based Bucketing**: Group normalized reviews into Positive (Score 4-5) and Negative (Score 1-3).
- **Multilingual Embeddings**: Use a local multilingual model (e.g., `paraphrase-multilingual-MiniLM-L12-v2` via `sentence-transformers`) to handle Hinglish (Romanized Hindi) and English text accurately.
- **Local Clustering**: Group semantically similar reviews into distinct themes locally to reduce LLM payload.

---

### Phase 2b: LLM Summarization via Groq (Rate Limit Conscious)
Use the Groq API (`llama-3.3-70b-versatile`) to summarize the local clusters and extract verbatim quotes.

> [!WARNING]
> **Groq API Limits**: 30 Requests per minute | 1K Requests per Day | 12K Tokens per minute | 100K Tokens per day.

#### [MODIFY] [src/core/processor.py](file:///c:/Projects/Groww/src/core/processor.py)
- **Representative Sampling**: Select only the top 3-5 most representative reviews per cluster to feed into the LLM, ensuring the total payload stays well under the 12,000 Tokens/Minute limit.
- **Rate Limiting & Retries**: Implement explicit `time.sleep()` delays and exponential backoff between Groq API calls to prevent 429 Rate Limit Errors.
- **LLM Prompting**: Extract theme naming, action items, and exactly 1-2 verbatim quotes per theme.

#### [NEW] [src/core/validator.py](file:///c:/Projects/Groww/src/core/validator.py)
- Strict verbatim checker to verify that LLM-extracted user quotes are exact substrings (or close fuzzy matches) of actual ingested review texts.

---

### Phase 3: Google Workspace Integration & Orchestration
Connect the orchestrator to Google Workspace MCP servers and manage execution state.

#### [NEW] [src/core/workspace.py](file:///c:/Projects/Groww/src/core/workspace.py)
- Google Docs MCP client integration: Appends report sections to the Groww Weekly Doc.
- Gmail MCP client integration: Sends teaser emails with deep links.

#### [NEW] [src/core/idempotency.py](file:///c:/Projects/Groww/src/core/idempotency.py)
- Checks the Google Doc outline for an existing `Week YYYY-Wxx` heading before running.
- Writes metadata to a local `data/run_history.json` tracking log.

#### [NEW] [src/cli.py](file:///c:/Projects/Groww/src/cli.py)
- Command-line entry point to trigger a run for the current week or backfill a specific historical ISO week.

---

### Phase 4: Testing & Deployment
Verification and automation steps.

#### [NEW] [tests/](file:///c:/Projects/Groww/tests)
- Mock tests for review fetching, PII scrubbing, clustering, and quote validation.
- End-to-end dry run scripts with mock MCP tool outputs.

---

## Verification Plan

### Automated Tests
- Run unit test suite:
  ```bash
  pytest tests/
  ```

### Manual Verification
- Dry runs across multiple weeks (e.g., `python src/cli.py --weeks 12 --dry-run`)
- Verifying the `data/run_history.json` logs correctly prevent duplicate appending on subsequent runs.
- Inspecting Google Doc formatting and Gmail delivery manually after deployment.

---

## Phase 5: Web Dashboard (FastAPI + React)

Build a full-stack dashboard to visually explore the generated pipeline data, bypassing the need to read plain text Google Docs.

### User Review Required
> [!IMPORTANT]
> - Do you want the frontend to be in a separate `dashboard/` directory, or served statically by the FastAPI backend? (Plan assumes separate `dashboard/` dir running via Vite dev server).
> - Do you want to use raw CSS for the glassmorphism/animations, or are you okay with using TailwindCSS + Framer Motion for rapid, high-quality animations? (Plan assumes raw CSS as per agent guidelines unless otherwise specified).

### Proposed Changes

#### [MODIFY] [src/cli.py](file:///c:/Projects/Groww/src/cli.py)
- Update the pipeline to dump the raw JSON of `valid_themes` into `data/themes_{iso_week}.json`. The backend needs structured data to serve to the frontend.

#### [NEW] [src/api/](file:///c:/Projects/Groww/src/api)
- `main.py`: A Python FastAPI backend with CORS enabled.
- `GET /api/runs`: Parses `data/run_history.json` to return a list of available weeks.
- `GET /api/themes/{iso_week}`: Reads `data/themes_{iso_week}.json` and returns the structured themes, quotes, and action items.
- `requirements.txt`: Add `fastapi` and `uvicorn`.

#### [NEW] [dashboard/](file:///c:/Projects/Groww/dashboard)
- Create a new React + Vite project.
- Implement a premium, glassmorphic UI using standard CSS (no Tailwind).
- **Features**:
  - Sidebar/Dropdown to select the historical Week (fetched from API).
  - Main Dashboard displaying Themes as beautiful interactive cards.
  - Expandable sections for Verbatim Quotes and Action Ideas.
  - Micro-animations on hover and click.
  - Dark mode by default using Google Fonts (Inter/Outfit).

### Verification Plan
- Run `uvicorn src.api.main:app` and verify the JSON endpoints return correct data.
- Run `npm run dev` in the dashboard folder and verify the UI looks premium, fetches data correctly, and transitions smoothly between weeks.
