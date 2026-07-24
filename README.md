# streamlit-rio-rentals

A Streamlit app for exploring Rio de Janeiro apartment rental listings on an
interactive map, with filters for neighborhood, rooms, parking spots,
suites, area, price, condo fee, and IPTU — plus a chat assistant that sets
those same filters from a natural-language request.

## Setup

```bash
uv sync
```

## Run

```bash
uv run streamlit run main.py
```

Open the local URL Streamlit prints (typically `http://localhost:8501`).

## Chat assistant configuration

The chat box is optional — the app works fully without it, using only the
manual filter controls. To enable it, set three environment variables in a
git-ignored `.env` file at the repo root (loaded automatically at startup
via `python-dotenv`), pointing at any OpenAI-compatible chat-completions
backend with tool-calling support:

```bash
# .env
LLM_BASE_URL=...   # e.g. your Ollama endpoint + /v1, or https://openrouter.ai/api/v1
LLM_API_KEY=...    # any placeholder for Ollama; a real key for OpenRouter
LLM_MODEL=...      # e.g. qwen3:8b (Ollama) or openai/gpt-4o-mini (OpenRouter)
```

Plain `export`ed shell variables also work and take precedence over `.env`
values.

Two backends have been confirmed working:

| Backend | `LLM_BASE_URL` | `LLM_API_KEY` | `LLM_MODEL` |
|---|---|---|---|
| Ollama | `<your Ollama endpoint>/v1` | any placeholder (ignored) | `qwen3:8b` |
| OpenRouter | `https://openrouter.ai/api/v1` | your real OpenRouter key | `openai/gpt-4o-mini` |

**Never commit an API key to this repo.** `.env` is git-ignored — keep
keys there or in shell environment variables, never in any tracked file.
If `LLM_BASE_URL`/`LLM_MODEL` are unset, the chat input is simply
disabled; the rest of the app is unaffected.

A debug toggle in the chat section (off by default) reveals the model's
raw reasoning trace and tool-call JSON for the most recent message, useful
for troubleshooting unexpected filtering behavior.

## Data

`data/dados_apartamentos_with_coordinates.csv` is the enriched listings
dataset the app reads. It's generated from `data/dados_apartamentos.csv` by
`scripts/enrich_coordinates.py`, which geocodes each neighborhood and adds a
small per-listing jitter so same-neighborhood listings are distinguishable
on the map:

```bash
uv run python scripts/enrich_coordinates.py
```

## Project docs

- `docs/plan-map-app.md` — original feature planning notes.
- `.specify/memory/constitution.md` — project principles and constraints.
- `specs/001-rental-map-filters/` — spec-kit spec, plan, and tasks for the
  map/filters feature.
- `specs/002-chat-filter-assistant/` — spec-kit spec, plan, and tasks for
  the chat assistant feature, including a `validation/` folder with the
  scripts used to verify LLM backend behavior before implementation.
