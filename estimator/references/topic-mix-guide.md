# Topic-mix guide: from a feature to topic blocks

How to turn one feature from a PRD into a `topic_blocks` spec. A block is one stretch of continuous work on one topic (see the measuring docs). A feature is a handful to a few dozen of them.

The block counts below are my starting heuristics, drawn from the patterns in my own work blocks. They are counts, not minutes: the minutes come from your benchmark table at run time. Replace them with your own counts once calibrate.py shows where they miss.

## The topics

| Topic | What it is | Signals in a PRD |
|---|---|---|
| `database_setup` | Schema, migrations, indexes, extensions | "tables", "schema", "migration", "vector extension", "indexes" |
| `database_query` | Select, insert, update and delete logic | "fetch the data", "queries", "report from the database" |
| `python_module` | A new module, class or script | "build a script", "library", "module", "service" |
| `python_test` | Unit and integration tests | "tests", "test coverage", "validation" |
| `parser_work` | Parsing files: PDF, spreadsheets, email, HTML, transcripts | "parse PDFs", "read Excel", "email parser", ".msg files" |
| `api_integration` | External API calls, OAuth, webhooks | "CRM API", "OAuth", "webhook", "REST integration", "GraphQL client" |
| `data_cleaning` | Deduplication, normalization, language detection, PII | "deduplicate", "clean the data", "detect language", "redact PII" |
| `frontend_work` | Components, pages, UI state | "dashboard", "frontend", "UI", "component", "page" |
| `documentation` | READMEs, API docs, user guides | "documentation", "README", "user guide" |
| `deployment` | CI/CD, containers, hosting | "deploy", "CI/CD", "Dockerize", "serverless functions" |
| `bug_fix` | Debugging. Reserve it, do not plan it as a feature | Reserve 15 to 25% of the total, or add `bug_fix` blocks to risky features |
| `analysis_only` | Reading, searching, planning without code | Produced by the classifier; rarely something you estimate |

These are the topic names behind my table. If your work does not fit them (a Go service, a mobile app), rename or add topics in the classifier rules and use the same names here. The estimator only needs the names in your features to match the names in your table.

## Block counts per feature type

### Data ingest connectors

**Simple connector** (one source, one file type, no auth): `parser_work` 3, `python_test` 2. Total 5 blocks.

**Standard connector** (one source, mixed file types, OAuth):
- `parser_work` 4 to 6
- `api_integration` 4 to 8, depending on the OAuth flow
- `python_test` 3 to 5
- `python_module` 1 to 2 for helpers
- one external dependency

Total 12 to 22 blocks.

**Complex multi-source** (custom CRM objects, document-store permissions):
- `parser_work` 6 to 10
- `api_integration` 8 to 14
- `python_test` 4 to 7
- `data_cleaning` 2 to 4
- `python_module` 2 to 3
- two or three external dependencies

Total 22 to 40 blocks.

### Retrieval (RAG) components

| Component | Blocks |
|---|---|
| Vector index setup (vector extension plus an HNSW index) | `database_setup` 3 to 5, `python_test` 2 to 3 |
| Chunking and embedding pipeline | `python_module` 4 to 6, `python_test` 3 to 4, `api_integration` 2 to 3 (the embedding API) |
| MCP retrieval server (one or two tools, auth) | `python_module` 4 to 6, `python_test` 3 to 5, `documentation` 1 to 2, one external dependency |
| Hybrid retrieval (keyword plus vector plus metadata filter) | `python_module` 6 to 10, `python_test` 4 to 6, `database_query` 2 to 4 |
| Evaluation loop (10 to 20 queries plus metrics) | `python_module` 4 to 6, `python_test` 3 to 5, `documentation` 1 to 2 |

### Frontend

| Component | Blocks |
|---|---|
| Simple page or single component | `frontend_work` 2 to 3, one test block |
| Dashboard with 3 to 5 tabs and state management | `frontend_work` 5 to 10, `python_test` 3 to 5 (backend), `api_integration` 2 to 4 (frontend to backend), `documentation` 1 |
| Multi-tab dashboard with auth and permissions | `frontend_work` 10 to 20, `api_integration` 4 to 6, `python_test` 5 to 7, `documentation` 1 to 2 |

### Deployment

| Component | Blocks |
|---|---|
| Static or serverless hosting, no database | `deployment` 2 to 3, `documentation` 1 |
| Cloud production deploy with database, auth and monitoring | `deployment` 4 to 7, `python_test` 2 to 3 (smoke tests), `documentation` 2 to 3 (runbook) |

## Quality target

The quality factor multiplies a feature's block minutes:

| `quality_target` | Factor | When |
|---|---:|---|
| `poc` | 1.0 | Prototype: no tests, no docs |
| `demo` | 1.4 | Works for a demo, basic tests, light docs |
| `production-ready` | 2.2 | Full tests, error handling, security, docs, monitoring |

In my experience a production-ready version takes 2.5 to 4 times the blocks of a proof of concept. The factors are smaller than that because the measured medians already mix all quality levels. They live in the config file (`quality_factors`), and calibrate.py tells you when yours are off.

## External dependencies

Every external API, auth flow or non-public schema costs connection probing before any feature code works. List them in `external_deps`; each adds a fixed number of minutes:

| `external_deps` value | Minutes | What it is |
|---|---:|---|
| `rest_api_key` | 15 | A REST API with an API key |
| `oauth2` | 30 | A standard OAuth 2.0 flow |
| `non_public_schema` | 30 | A database schema the API does not expose, needing a proxy function or extra config |
| `enterprise_oauth` | 45 | An enterprise identity platform with tenant consent |
| `custom_legacy_auth` | 60 | Custom or legacy auth |
| `streaming_api` | 75 | A streaming or realtime API (WebSockets and the like) |
| anything else | 25 | The default premium |

These are my starting values, set after measured connection probes, not a measurement in themselves. Add your own types in the config file (`external_dep_premiums`).

## Dependencies between features

Sequential by nature:
- schema before ingest pipelines, because ingest needs the tables;
- vector index before the embedding pipeline;
- retrieval server before the evaluation loop;
- a stable backend before frontend integration.

Parallel by nature:
- several ingest connectors, which share nothing;
- frontend, evaluation and deploy once the backend is stable;
- documentation and tests, in any phase.

On the critical path by nature: schema design, architecture decisions (chunking strategy, retrieval algorithm) and the production deploy.

## Common features as topic mixes

| Feature | Mix |
|---|---|
| CRM email field sync | `parser_work` 3, `api_integration` 5, `python_test` 3, `external_deps: ["oauth2"]` |
| Chat interface with source citations | `frontend_work` 8, `api_integration` 3, `python_test` 3, depends on the retrieval server |
| PDF processing for a large document set | `parser_work` 6, `python_module` 3, `python_test` 4, `data_cleaning` 3 |
| Multi-tenant access control | `database_setup` 3, `python_module` 5, `python_test` 6, `api_integration` 2 |
| Daily ETL job orchestrator | `python_module` 6, `deployment` 3, `python_test` 4, `documentation` 2 |

## When to ask instead of guessing

- **Legacy codebase.** A mature or legacy codebase is slower to change than a fresh one. Ask for an `extra_factor`; my own notes use 1.10 to 1.20 for legacy systems.
- **Unclear mix.** If the feature description does not say what gets built, ask for the concrete deliverables.
- **Unclear quality target.** Proof of concept against production is a 2 to 4 times difference in blocks. Ask.
- **No history.** If the feature needs work your table has no blocks for (compliance audits, a new platform), say so in the report instead of borrowing a topic that looks close.
