# Decision Log

## 1. Assumptions and Why

- **The highest-value path was a reliable conversational analysis loop.** The task emphasizes follow-up questions, relevant analysis, and a written explanation, so I prioritized the path from user question to schema-aware SQL, query results, and a readable answer over building a broad analytics surface.
- **The public dataset still requires application-side BigQuery configuration.** Although the GA4 dataset is public, running queries requires a Google Cloud project, billing, and credentials. I treated that setup as part of the application's deployment requirements and kept credentials outside the repository.
- **The agent should be constrained to read-only analysis.** The model can inspect the GA4 schema and execute SQL, but the SQL tool only accepts `SELECT`/`WITH` queries, rejects multiple statements and write keywords, and caps returned rows. This was a pragmatic safety and cost boundary for an assessment prototype.
- **A bounded, manually implemented loop was sufficient for the time box.** I implemented the agent loop directly with Gemini's SDK, disabled automatic function calling, handled tool responses explicitly, and capped the loop at eight turns. This keeps the control flow inspectable and satisfies the no-agent-framework requirement.
- **Gemini was an acceptable first provider.** I chose it to get the end-to-end agent working quickly, with an environment-configurable primary model and fallback models for transient provider failures. I assumed provider abstraction was less important than demonstrating the core workflow in the initial version.

## 2. Cut or Deprioritized

I intentionally limited visualization support to vertical bar charts. Line, stacked, pie, and other chart types would improve the analytical experience, but they were secondary to fetching trustworthy data and explaining it in conversation. The prompt also instructs the agent to use prose or Markdown tables when a bar chart is not a good fit, so the application still has a useful fallback for trends, exact values, and multi-metric answers.

I also deprioritized a full frontend test suite and advanced product features such as authentication, saved conversations, query history, caching, and a richer data-exploration UI. The current submission focuses testing and validation effort on the backend/agent boundary and SQL safety; frontend automated coverage remains an intentional follow-up rather than a claim of completeness.

## 3. Where I Got Stuck and What I Did

The most time-consuming part was deployment and environment setup rather than the agent logic. The project needed a React/Vite frontend, a FastAPI backend, BigQuery credentials, an LLM API key, local environment files, and separate hosting concerns. I also had to make the repository structure work for both local development and deployment, prepare the backend for Cloud Run, and configure the frontend to reach the deployed API without exposing secrets.

I handled this incrementally: first establishing a basic working agent, then separating frontend and backend responsibilities, adding streamed status events for a better chat experience, tightening SQL validation, adding model fallbacks, and finally documenting local setup and the deployed application. This approach let me keep a usable end-to-end path while resolving infrastructure issues one at a time.

## 4. What I Would Build With 40 More Hours

1. **An evaluation and A/B testing harness.** I would create a fixed set of representative ecommerce questions with expected properties, capture generated SQL, tool calls, latency, cost, answer quality, and chart suitability, then compare prompt versions systematically instead of relying mainly on manual checks.
2. **Provider and model selection.** I would introduce a small provider interface so Gemini, OpenAI, and Anthropic models could be configured or selected per request. The evaluation harness would show which model performs best for schema discovery, SQL generation, explanation quality, and follow-up context.
3. **Richer, validated visualizations.** I would support line charts for time series, horizontal bars for long labels, and additional composition/comparison views, with a typed chart schema validated on the server and client. The agent should choose a chart only when it improves the takeaway.
4. **Production-grade reliability and security.** I would add backend unit/integration tests, frontend interaction tests, structured error reporting, query cost/time limits, stricter CORS and secret management, request cancellation, and conversation persistence.
5. **A stronger analytical workflow.** I would add query/result caching, explicit citations of the queried fields and date range, and a compact history of the analysis steps so users can inspect and reproduce how an answer was produced.