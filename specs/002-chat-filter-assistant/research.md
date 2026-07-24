# Phase 0 Research: Chat Filter Assistant

## 1. LLM client library and tool schema declaration

- **Decision**: Use the `openai` Python SDK purely as an OpenAI-compatible
  HTTP client, with `base_url` pointed at the configured backend
  (self-hosted Ollama by default, OpenRouter as an alternative) and
  `api_key` read from configuration (a placeholder string like `"ollama"`
  works for Ollama, which doesn't validate it; a real key is required for
  OpenRouter). Each tool's arguments are declared as a plain
  `pydantic.BaseModel` (`SetNeighborhoodsArgs`, `SetNumericRangeArgs`,
  `ResetFiltersArgs` — see `contracts/tools.md`); `BaseModel.model_json_schema()`
  generates the JSON schema sent in `tools=[...]`, and
  `BaseModel.model_validate_json()` parses/validates the model's returned
  tool-call arguments. The full `pydantic-ai` package (with its `Agent`
  abstraction and automatic tool-execution loop) was evaluated and
  deliberately **not** adopted — see decision #3 below and
  `validation/README.md`.
- **Rationale**: Both backends implement the same chat-completions +
  tool-calling wire format, so one client library covers both with zero
  code branching — only `base_url`/`api_key`/`model` differ. Verified live
  against the user's Ollama endpoint (`qwen3:8b`) and OpenRouter
  (`openai/gpt-4o-mini`): a single
  `client.chat.completions.create(..., tools=[...], tool_choice="auto")`
  call correctly applies multi-criteria prompts, including translating "2
  bedroom" into `rooms: {min: 2, max: 2}` (satisfying FR-005) without a
  system prompt — the instruction lives directly in the tool's
  description, reinforced by the schema itself. Separately verified that
  Pydantic-generated schemas are accepted as-is by the backend (the extra
  per-property `"title"` fields Pydantic adds are harmless) and that
  `model_validate_json()` cleanly validates the returned arguments —
  giving typed, validated tool calls without adopting a full agent
  framework (`validation/05_pydantic_schema_generation.py`).
- **Alternatives considered**: Raw `httpx`/`requests` calls — would work
  identically since it's just JSON over HTTP, but the `openai` SDK gives
  typed response parsing (tool call arguments, etc.) for free; no reason to
  hand-roll it. Hand-written JSON schema dicts (no Pydantic) — works (this
  is what the first several validation scripts used), but schema and
  validation/dispatch logic can silently drift apart over time; a
  `BaseModel` makes them the same source of truth. Full `pydantic-ai`
  `Agent` framework — evaluated live and rejected for this feature; see
  decision #3.

## 2. Surfacing the model's reasoning trace (FR-010)

- **Decision**: Read `message.reasoning` (falls back to
  `message.model_extra.get("reasoning")` if the attribute access ever
  changes across SDK versions) defensively with `getattr(...,
  None)`. When absent (e.g. a backend/model that doesn't emit one), the
  debug panel shows only the raw tool-call JSON and a note that no
  reasoning trace was provided.
- **Rationale**: Verified live — `qwen3:8b` via Ollama returns a
  `reasoning` field that is not part of the standard OpenAI response
  schema, but the `openai` SDK's permissive pydantic model still exposes it
  (confirmed via `hasattr(message, "reasoning")` and `message.model_extra`
  both being populated). Since this is a non-standard extension, it can't be
  assumed present for every model/backend — confirmed live: OpenRouter's
  `openai/gpt-4o-mini` has the same `reasoning` attribute present (so
  `getattr` never raises) but its value is `None`, so the debug view must
  handle both "attribute missing" and "attribute present but empty".
- **Alternatives considered**: Parsing reasoning out of `message.content`
  — unnecessary; the backend already provides it as a structured field for
  this model.

## 3. Tool-calling shape: single call, no agentic loop, no PydanticAI Agent

- **Decision**: Each chat turn is exactly one
  `chat.completions.create(...)` call via the raw `openai` SDK. The
  returned `tool_calls` are parsed/validated via the Pydantic `BaseModel`s
  from decision #1 and executed directly against `st.session_state` (they
  mutate filter state, they don't need to return data to the model), and
  the confirmation message is generated deterministically in Python from
  what was executed — the model is never called a second time to "see"
  tool results or summarize them. The full `pydantic-ai` package was
  evaluated live against this exact scenario and **rejected**: its
  `Agent.run()` executes tools itself, then makes a *second* model call to
  synthesize final text from the tool results
  (`validation/04_pydantic_ai_ollama.py` — confirmed via `result.usage`:
  `requests=2`). This feature has no use for that second call, since the
  reply is already generated deterministically; in the live test it also
  cost ~1,800 extra output tokens and still didn't improve tool-call
  accuracy (the `rooms` filter was still missed on that run). Net: keep
  the one-call design, but layer plain Pydantic models on top of it
  (decision #1) rather than hand-written schema dicts.
- **Rationale**: Our tools are pure state-setters (`set_neighborhoods`,
  `set_numeric_range`, `reset_filters`) with no return value the model
  needs to reason over further, so a full agentic tool-result-feedback loop
  would add latency and a second failure point for zero benefit. A
  deterministic Python summary is also more reliable than asking the model
  to self-summarize (avoids hallucinated summaries of what changed), which
  directly serves FR-006.
- **Alternatives considered**: Multi-turn loop (send tool results back,
  let the model produce the final reply) — rejected as unnecessary
  complexity and an extra reliability risk for a case that doesn't need
  it. Full `pydantic-ai` `Agent` framework — live-tested, rejected for the
  reasons above; worth revisiting specifically for a possible future
  advisor/professional persona that needs a genuinely *synthesized*
  structured answer (e.g. a pricing recommendation), which is the case
  its two-call design is actually built for — not for this feature's
  direct UI-state tool calls.
- **Known limitation (accepted for v1)**: since only the current message is
  sent (no prior chat turns), incremental refinement works for *additive*
  follow-ups (e.g. "also limit to 2 rooms" correctly adds a rooms filter
  on top of whatever's already in `st.session_state` from earlier turns),
  but the model can't resolve pronoun/referential follow-ups like "change
  that to Ipanema instead" since it has no memory of what "that" refers
  to, and there's no tool to unset a single field short of `reset_filters`
  clearing everything. Not addressed by any FR in this spec; flagged here
  as a natural next iteration rather than silently left unmentioned.

## 4. Programmatically updating filter widgets from chat (FR-003)

- **Decision**: Every filter widget is given an explicit, stable `key=`
  (the neighborhood `st.multiselect` currently has none — this must be
  added, e.g. `key="Bairro"`; the numeric `st.number_input` pairs already
  use `key=f"{column}_min"/"_max"`). The chat-processing code runs *before*
  the filter widgets are instantiated in `main.py`'s top-to-bottom script
  order, and directly assigns `st.session_state[key] = value` for every
  field a tool call touched. Because Streamlit gives session-state values
  precedence over a widget's `value=` argument once a key is set, the
  widgets simply render with the new values on that same rerun — no
  `st.rerun()` needed.
- **Rationale**: This is the standard, documented Streamlit pattern for
  programmatic widget control and needs no extra machinery; it does
  require reordering `main.py` slightly (chat section before filter
  section) and adding the one missing `key=`.
- **Alternatives considered**: Mutate widget values after they're
  instantiated — not possible in Streamlit (raises an exception:
  a widget's session-state value can't be changed after it's been
  instantiated in the same run). Using `st.rerun()` after setting state —
  unnecessary extra rerun when simply ordering the script correctly avoids
  it.

## 5. Resetting filters via chat (FR-007)

- **Decision**: `reset_filters()` (no arguments) deletes the relevant
  `st.session_state` keys (`Bairro` and each numeric field's `_min`/`_max`)
  before the widgets are instantiated. With no session-state entry present,
  each widget falls back to its existing default `value=` (full
  min/max, no neighborhoods selected), identical to a fresh page load.
- **Rationale**: Reuses the exact mechanism from #4 with no special-case
  code path for "reset" versus "set".
- **Alternatives considered**: Explicitly setting each key back to its
  full-range default — equivalent in effect but requires the reset
  function to know every field's bounds; deleting the keys is simpler and
  automatically stays correct if fields are ever added.

## 6. Configuration (FR-009)

- **Decision**: Three environment variables, read via `os.environ`:
  `LLM_BASE_URL` (required, no hardcoded default), `LLM_API_KEY` (optional,
  defaults to a placeholder string since Ollama ignores it), `LLM_MODEL`
  (required, no hardcoded default). One generic set of vars, not
  provider-specific names, since FR-009 only requires switching backend by
  editing config — the same 3 vars just point somewhere else:

  | Backend | `LLM_BASE_URL` | `LLM_API_KEY` | `LLM_MODEL` |
  |---|---|---|---|
  | Ollama (confirmed working) | the user's Ollama endpoint + `/v1` | any placeholder (ignored) | `qwen3:8b` |
  | OpenRouter (confirmed working) | `https://openrouter.ai/api/v1` | real OpenRouter key | `openai/gpt-4o-mini` |

  Both configurations were live-verified in this session with the same
  tool schemas and produced correct, equivalent tool calls (including the
  exact-count case). Secrets (the OpenRouter key) are never written to a
  repo file — only exported as a shell environment variable or placed in a
  git-ignored local file, consistent with not committing credentials.
  If `LLM_BASE_URL` or `LLM_MODEL` is unset, the chat input is disabled
  with a clear message instead of failing on first use.
- **Rationale**: Matches FR-009's resolved decision (fixed, deployment-time
  config, no in-app switcher) with the minimum needed to point at either
  backend; no new dependency needed since `os.environ` is stdlib.
- **Alternatives considered**: `python-dotenv` for local `.env` loading —
  unnecessary; the user can export env vars or use their shell/session
  config directly, and adding a dependency for this is not justified for a
  single-user local app. Provider-specific env var names (e.g.
  `OPENROUTER_API_KEY`) — rejected in favor of generic `LLM_*` names so the
  app code never needs to know or care which backend is configured.

## 7. Error handling for an unreachable/erroring backend (FR-013)

- **Decision**: Wrap the `chat.completions.create(...)` call in a
  try/except; on any exception, show `st.error(...)` in the chat area with
  the exception's message, make no filter changes for that turn, and leave
  the rest of the page (manual filters, map, table) rendering exactly as
  it would without the chat feature.
- **Rationale**: Directly satisfies FR-013 and SC-005; since chat
  processing happens before the filter/map/table section, an exception
  caught there simply skips filter mutation and falls through to normal
  rendering.
- **Alternatives considered**: A retry loop — rejected as unnecessary
  complexity for a manual, single-user chat interaction (the user can just
  resend their message).
