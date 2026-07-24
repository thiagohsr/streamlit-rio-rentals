# Phase 1 Data Model: Chat Filter Assistant

All of this is in-memory, session-scoped state (`st.session_state`) — none
of it is persisted to disk, per FR-014.

## Entity: Chat Turn

One exchange, appended to `st.session_state["chat_history"]` (a list) for
rendering the conversation.

| Field | Type | Notes |
|---|---|---|
| role | `"user"` \| `"assistant"` | Who sent it. |
| content | string | The message text. For the assistant, this is the deterministic confirmation message (research.md #3), not raw model output. |

Note: the underlying LLM message history sent to the API on each call is
just the current user message (research.md #3 — single-call design, no
multi-turn context needed since each request is filtered independently);
`chat_history` here is purely for on-screen display.

## Entity: Filter Update (Tool Call)

The structured result of one tool call, applied directly to the existing
filter widgets' `st.session_state` keys (see feature 001's data-model.md
Active Filter Set, which these keys already back). Each tool's raw JSON
arguments are first parsed into the corresponding Pydantic `BaseModel`
from `contracts/tools.md` (`SetNeighborhoodsArgs`, `SetNumericRangeArgs`,
`ResetFiltersArgs`) via `model_validate_json()` — that model *is* the
argument schema below, not a separate description of it.

| Tool | Arguments (`BaseModel`) | Effect |
|---|---|---|
| `set_neighborhoods` | `SetNeighborhoodsArgs(names: list[str])` | `st.session_state["Bairro"] = names` |
| `set_numeric_range` | `SetNumericRangeArgs(field: FilterField, min: float, max: float)` | `st.session_state[f"{column}_min"] = min`, `st.session_state[f"{column}_max"] = max`, where `field` maps to the existing dataset column (`rooms`→`Quartos`, `parking_spots`→`Vagas`, `suites`→`Suites`, `area`→`Area`, `monthly_rent`→`Valor`, `condo_fee`→`Condominio`, `iptu`→`IPTU`) |
| `reset_filters` | `ResetFiltersArgs()` (no fields) | Deletes `Bairro` and every numeric field's `_min`/`_max` keys from `st.session_state`, letting widgets fall back to their defaults |

**Validation rules**:
- A `pydantic.ValidationError` while parsing a tool call's raw arguments
  (e.g. `field` outside the `FilterField` enum, missing required key) is
  caught in `apply_tool_call`; that individual tool call is treated as
  not applied and reported the same way as "no matching filter found"
  (FR-008), without crashing the turn or the other tool calls in it.
- Once parsed and type-valid, `set_numeric_range`'s `min`/`max` are
  further clamped to the column's actual observed min/max before being
  written to session state (Pydantic validates *shape*, not dataset
  bounds — a structurally valid but out-of-range value still shouldn't
  reach the widget as-is).
- `set_neighborhoods`' `names` not matching any known `Bairro` value are
  dropped, and the confirmation message notes which (if any) were
  unrecognized (spec's Edge Cases: unknown neighborhood name).

## Entity: Debug Trace

Held in `st.session_state["last_debug"]`, overwritten every turn (FR-010:
most-recent-turn only, not full history).

| Field | Type | Notes |
|---|---|---|
| reasoning | string \| `None` | From `message.reasoning` if the backend provided one (research.md #2). |
| tool_calls_raw | list of `{name, arguments}` | The raw tool-call name + JSON-string arguments exactly as returned, before any parsing/clamping/mapping. |
| error | string \| `None` | Set instead of the above two if the LLM call failed (research.md #7). |

Rendered only when the debug toggle (`st.session_state["show_debug"]`,
default `False`) is on.
