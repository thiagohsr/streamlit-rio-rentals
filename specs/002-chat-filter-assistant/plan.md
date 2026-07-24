# Implementation Plan: Chat Filter Assistant

**Branch**: `002-chat-filter-assistant` | **Date**: 2026-07-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-chat-filter-assistant/spec.md`

## Summary

Add a chat box to the existing Streamlit app that lets a user describe what
they want in natural language; an LLM (self-hosted Ollama by default,
OpenRouter as a documented alternative — both OpenAI-compatible, both
confirmed to support tool-calling) turns that into one or more tool calls
that directly set the app's existing filter widgets. Each turn gets a
deterministic, Python-generated plain-language confirmation of what changed.
A debug toggle (off by default) exposes the model's raw reasoning and raw
tool-call JSON for the most recently completed turn only, to help debug
behavior ahead of a real eval/tracing setup.

## Technical Context

**Language/Version**: Python >= 3.13 (unchanged from feature 001)

**Primary Dependencies**: `streamlit`, `pandas`, `pydeck` (existing) plus
**new**: `openai` — used purely as an OpenAI-compatible HTTP client (its
`base_url` is pointed at the configured Ollama or OpenRouter endpoint; no
OpenAI service is actually used) — and `pydantic` — used to declare each
tool's argument schema as a `BaseModel` (auto-generating the JSON schema
sent to the model, and validating its returned arguments), without the
full PydanticAI `Agent`/tool-execution-loop framework (see
`validation/README.md` for why that was tried and rejected: it costs a
second, unneeded model call per turn with no demonstrated accuracy
benefit for this feature's state-mutating tools).

**Storage**: Unchanged flat-file CSV for listings. New in this feature:
chat history and the most-recent debug trace live only in
`st.session_state` (per FR-014, no persistence beyond the session).

**Testing**: Manual verification per constitution Principle V, using
`quickstart.md`'s scenarios against the real, already-confirmed Ollama
endpoint (`qwen3:8b`).

**Target Platform**: Unchanged — local/dev browser via Streamlit's built-in
server.

**Project Type**: Single-page web app, now split across two files (see
Structure Decision) as it grows past feature 001's single-file threshold.

**Performance Goals**: A chat round-trip should complete and update filters
within a few seconds against a local Ollama call — no request left
unacknowledged (SC-003). No hard numeric latency target is set since this
hasn't been formally load-tested; this is a single-user local app.

**Constraints**: LLM backend/model is fixed, deployment-time configuration
via environment variables only, no in-app switcher (FR-009); chat history
and debug data are session-only, never written to disk (FR-014); the
manual filter controls must keep working even if the LLM backend is
unreachable (FR-013); dependencies only via `uv add` (constitution
Principle II); all new code in English (Principle III).

**Scale/Scope**: Same dataset as feature 001 (~18,780 listings, 145
neighborhoods). Adds: one chat input/history area, one debug toggle +
panel, and 3 LLM-facing tools (`set_neighborhoods`, `set_numeric_range`,
`reset_filters`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Reproducible Data Pipeline | PASS | This feature never touches `data/`; it only reads the already-loaded listings DataFrame and adjusts filter state. |
| II. uv-Managed Dependencies | PASS | `openai` and `pydantic` added via `uv add openai pydantic`; the full `pydantic-ai` package was evaluated live (see `validation/`) and deliberately not added. env vars read via stdlib `os`. |
| III. English-Only Code & Naming | PASS | All new identifiers (`chat.py`, `set_neighborhoods`, `set_numeric_range`, `reset_filters`, etc.) are English; only literal `Bairro` values stay Portuguese. |
| IV. Spec-Driven Feature Development | PASS | This plan follows `specify` (spec.md, all 3 clarifications resolved) and precedes `tasks`/`implement`. |
| V. Simplicity & Verify-in-Browser | PASS | See Structure Decision for the one deliberate split (main.py -> main.py + chat.py), justified by size, not spec creep. `quickstart.md` requires a real, running Ollama round-trip before calling this done. |

No unjustified violations. Complexity Tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-chat-filter-assistant/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── tools.md          # Phase 1 output: the 3 LLM-facing tool schemas
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
main.py                  # Existing UI: page config, data loading, filter
                          # widgets, map, results table. Extended with a
                          # chat section (renders history, calls chat.py,
                          # renders the debug panel when toggled on).
chat.py                  # NEW: LLM client setup from env vars, the 3 tool
                          # JSON schemas, the single-call request/response
                          # handling, tool execution against
                          # st.session_state, and deterministic
                          # confirmation-message generation.
data/                    # Unchanged
scripts/                 # Unchanged
```

**Structure Decision**: Split into `main.py` (UI/layout, unchanged
responsibilities) + new `chat.py` (LLM integration). Feature 001's plan
flagged splitting once the app "grows past roughly 250-300 lines"; adding
LLM client setup, tool schemas, tool execution, and debug-trace handling to
`main.py` in place would clearly cross that line and mix concerns (page
layout vs. LLM integration), so the split happens now rather than
speculatively earlier.

## Complexity Tracking

*No constitution violations — table not needed.*
