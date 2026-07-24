# Tool Contracts: Chat Filter Assistant

Each tool's arguments are declared once as a `pydantic.BaseModel` — the
single source of truth for both the JSON schema sent to the model and the
validation applied to its response (research.md #1). The JSON schema shown
under each tool is what `BaseModel.model_json_schema()` actually produces
(live-verified against both configured backends, Ollama/`qwen3:8b` and
OpenRouter/`openai/gpt-4o-mini` — see
`validation/05_pydantic_schema_generation.py`); it is generated at import
time in `chat.py`, never hand-maintained separately from the models below.

## `set_neighborhoods`

```python
class SetNeighborhoodsArgs(BaseModel):
    names: list[str]
```

Description sent to the model: *"Set the neighborhood (Bairro) filter to
one or more neighborhood names."*

Generated schema:

```json
{
  "type": "object",
  "properties": {
    "names": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["names"]
}
```

**Effect**: `st.session_state["Bairro"] = names` (after dropping any name
that doesn't match a known `Bairro` value — see data-model.md validation
rules).

## `set_numeric_range`

```python
FilterField = Literal[
    "rooms", "parking_spots", "suites", "area",
    "monthly_rent", "condo_fee", "iptu",
]

class SetNumericRangeArgs(BaseModel):
    field: FilterField
    min: float
    max: float
```

Description sent to the model: *"Set a min/max range filter for one
numeric listing field. For an exact value (e.g. \"2 bedrooms\"), set min
and max to the same number."*

Generated schema:

```json
{
  "type": "object",
  "properties": {
    "field": {
      "type": "string",
      "enum": ["rooms", "parking_spots", "suites", "area", "monthly_rent", "condo_fee", "iptu"]
    },
    "min": { "type": "number" },
    "max": { "type": "number" }
  },
  "required": ["field", "min", "max"]
}
```

**Effect**: maps `field` to the dataset column (`rooms`→`Quartos`,
`parking_spots`→`Vagas`, `suites`→`Suites`, `area`→`Area`,
`monthly_rent`→`Valor`, `condo_fee`→`Condominio`, `iptu`→`IPTU`), clamps
`min`/`max` to that column's observed bounds, then sets
`st.session_state[f"{column}_min"]` / `st.session_state[f"{column}_max"]`.

**Note on the description field**: the explicit "for an exact value, set
min and max to the same number" instruction lives directly in the tool's
description string (not a separate system prompt), since that's what the
model actually conditions on for every call — this is the primary
mechanism satisfying FR-005.

## `reset_filters`

```python
class ResetFiltersArgs(BaseModel):
    pass
```

Description sent to the model: *"Clear all filters currently set (via
chat or manually) back to their defaults, showing every listing again."*

Generated schema:

```json
{
  "type": "object",
  "properties": {}
}
```

**Effect**: deletes `st.session_state["Bairro"]` and every numeric field's
`_min`/`_max` keys, letting the widgets fall back to their default values
on the next render (data-model.md #5).

## Parsing and validating a tool call

```python
ARG_MODELS = {
    "set_neighborhoods": SetNeighborhoodsArgs,
    "set_numeric_range": SetNumericRangeArgs,
    "reset_filters": ResetFiltersArgs,
}

parsed = ARG_MODELS[tool_call.function.name].model_validate_json(
    tool_call.function.arguments
)
```

A `pydantic.ValidationError` here (malformed/out-of-enum arguments from the
model) is caught by `apply_tool_call` and treated the same as "no matching
filter found" for that individual tool call, rather than crashing the turn
— consistent with FR-008's "inform, don't error" requirement.

## Request shape (every chat turn)

```json
{
  "model": "<LLM_MODEL>",
  "messages": [{"role": "user", "content": "<the user's chat message>"}],
  "tools": [<the 3 generated schemas above, wrapped as {"type": "function", "function": {...}}>],
  "tool_choice": "auto"
}
```

Single message per request, single request per turn (research.md #3 — no
multi-turn history sent to the model, and no second "synthesis" call as a
full agent framework would make; each request is filtered independently
of prior turns).
