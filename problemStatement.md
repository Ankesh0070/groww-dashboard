# Weekly Product Review Pulse — Problem Statement

We are building an automated weekly “pulse” that turns public Google Play reviews for Groww into a one-page insight report and delivers it to stakeholders through Google Workspace, using MCP (Model Context Protocol) so that reviews are ingested and writes to Google Docs and Gmail go through dedicated MCP servers—not ad hoc API calls inside the agent.

**Supported product:** Groww.

## Objective
Give product, support, and leadership teams a repeatable, weekly snapshot of what customers are saying in store reviews: themes, representative quotes, and actionable ideas—without manual copy-paste or one-off spreadsheets.

## What the system does
- **Ingest public reviews** from the last 8–12 weeks (configurable window) from Google Play for Groww using a custom Google Play Store reviews MCP server provided within this project.
- **Cluster and rank feedback** using embeddings and density-based clustering (e.g. UMAP + HDBSCAN), then use an LLM to name themes, pull verbatim quotes, and propose action ideas—with validation so quotes must appear in real review text.
- **Render a concise one-page narrative**: top themes, quotes, action ideas, and a short “who this helps” section.
- **Deliver outputs only through Google Workspace MCP servers**:
  - **Google Docs MCP** — append each week’s report as a new dated section to a single running document for Groww (e.g. Weekly Review Pulse — Groww). The Doc is the system of record and preserves history.
  - **Gmail MCP** — send a short stakeholder email that includes a deep link to the new section in that Doc (heading link), not a duplicate full report in email alone.

### Architecture Concerns

| Concern | Where it lives |
| :--- | :--- |
| **Data retrieval** | Play Store reviews MCP server (custom server in project) |
| **Reasoning** | Clustering + LLM summarization (themes, quotes, actions) |
| **Output generation** | Report + email rendering (structured for Docs and HTML/text for Gmail) |
| **Human-visible delivery** | MCP tools only → Google Docs MCP + Gmail MCP |

*Note: The agent is an MCP host/client; it does not embed credentials or call the Docs/Gmail/Play Store APIs directly—all data access and delivery are mediated via dedicated MCP servers (including the custom Play Store reviews MCP server).*

## Key requirements
- **MCP-based ingestion and delivery**: Fetch Google Play reviews using the custom Play Store reviews MCP server tools, and append to the shared Google Doc and send Gmail only via their respective MCP servers’ tools (e.g. document batch update, draft/create/send flows as defined in architecture).
- **Weekly cadence**: Designed to run once per week (e.g. scheduled job Monday morning IST), with a CLI for backfill of any ISO week.
- **Idempotent runs**: Re-running the same ISO week must not create duplicate Doc sections or duplicate sends. This is enforced with a stable section anchor in the Doc and a run-scoped idempotency check on email (see architecture).
- **Auditable**: Each run records delivery identifiers (e.g. doc heading / message ids) and enough metadata to answer “what was sent when, for which week?”
- **Safety and quality**: PII scrubbing on review text before LLM and before publishing; reviews treated as data, not instructions; cost/token limits per run.

## Non-goals (explicit)
- A generic Google Workspace product beyond what the pulse needs (Docs append + Gmail send/draft).
- Real-time streaming analytics or a BI dashboard (the running Google Doc is the living artifact).
- Social sources (Twitter, Reddit, etc.) in the initial scope.
- Storing Google OAuth secrets in the agent codebase—they belong in the MCP servers’ configuration, per architecture.

## Who this helps

| Audience | Value |
| :--- | :--- |
| **Product** | Prioritize roadmap from recurring themes |
| **Support** | Spot repeating complaints and quality issues |
| **Leadership** | Fast health snapshot tied to customer voice |

## Sample output (illustrative)

> **Groww — Weekly Review Pulse**
> *Period: Last 8–12 weeks (rolling window)*
> 
> **Top themes**
> - **App performance & bugs** — Lag, crashes during trading hours; login/session timeouts.
> - **Customer support friction** — Slow responses; unresolved tickets.
> - **UX & feature gaps** — Confusing navigation for portfolio insights; missing advanced analytics.
> 
> **Real user quotes**
> - “The app freezes exactly when the market opens, very frustrating.”
> - “Support takes days to reply and doesn’t solve the issue.”
> - “Good for beginners but lacks detailed analysis tools.”
> 
> **Action ideas**
> - **Stabilize peak-time performance** — Scale infra during market hours; improve crash visibility.
> - **Improve support SLA visibility** — Expected response time in-app; ticket status tracking.
> - **Enhance power-user features** — Advanced portfolio analytics; clearer investments navigation.
> 
> **What this solves**
> Same intent as today: roadmap alignment for product, issue clustering for support, and a leadership-friendly snapshot—now automated, archived in Google Docs, and announced by email with a link back to the canonical section.

## Delivery expectations (stakeholder-facing)
- Each run adds one clearly labeled section to the Groww pulse Google Doc (dated / week-labeled).
- The email is a brief teaser (e.g. top themes as bullets) plus a “Read full report” link to that section.
- Development/staging may default to draft-only email until explicit confirmation to send, per implementation plan.
