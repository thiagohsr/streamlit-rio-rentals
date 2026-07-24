# Validation Scripts: Chat Filter Assistant

One-off spike scripts used during this feature's Phase 0 research, kept
here (rather than thrown away) so the reasoning behind `research.md`'s
decisions is traceable to real, reproducible runs against the actual
backends — not just claims. None of these are part of the shipped app;
`chat.py` doesn't import anything from here.

Run each with its own header comment's instructions. None require
committing secrets — API keys are always read from an env var, never
hardcoded.

| Script | Step | What it checked | Feeds into |
|---|---|---|---|
| `01_raw_tool_calling_ollama.sh` | 1 | Is the user's self-hosted Ollama endpoint reachable, and does `qwen3:8b` support OpenAI-compatible tool calling at all? | Initial feasibility answer; research.md #1 |
| `02_openai_sdk_ollama_reasoning.py` | 2 | Does the `openai` Python SDK (not just raw curl) expose Qwen3's non-standard `reasoning` field? | research.md #1, #2 |
| `03_openai_sdk_openrouter.py` | 3 | Does the identical `openai` SDK code path work unchanged against OpenRouter, and what happens to `reasoning` on a model that doesn't provide one? | research.md #1, #2 |
| `04_pydantic_ai_ollama.py` | 4 | Should we rework the feature around the full PydanticAI `Agent`/tool framework instead of the raw SDK? | research.md #1, #3 (see finding below) |
| `05_pydantic_schema_generation.py` | 5 | Does declaring tool arguments as plain `pydantic.BaseModel`s (schema generation + response validation) work as a middle ground, without the full `Agent` framework? | research.md #1, #3; contracts/tools.md; data-model.md |

## Key findings

- **Tool calling works on both backends** (steps 1-3): Ollama/`qwen3:8b`
  and OpenRouter/`openai-gpt-4o-mini` both correctly execute the same tool
  schemas via the same `openai` SDK call shape — confirms one client
  library covers both with just a `base_url`/`api_key`/`model` swap.
- **The model doesn't always call every expected tool** (step 1): a
  request naming 3 filter dimensions ("2 bedroom", a neighborhood, a rent
  range) sometimes only produces 2 tool calls, missing the exact-count
  translation for "2 bedroom" → a `rooms` range. This motivated writing
  the exact-count instruction directly into `set_numeric_range`'s
  description (see `contracts/tools.md`), not just a system prompt.
- **`reasoning` is backend-dependent, not just model-dependent** (steps
  2-3): present and populated for Ollama/qwen3, present as an attribute
  but `None` for OpenRouter/gpt-4o-mini. The debug view (FR-010) has to
  handle both "attribute missing" and "attribute present but empty".
- **PydanticAI's `Agent.run()` costs a second model call per turn that
  this feature doesn't need** (step 4): its default loop is
  tool-decision-and-execute, then a *second* call to synthesize final
  text from the tool results. This feature already generates the
  user-facing confirmation deterministically from what was actually
  executed (research.md #3), so that second call's output would be
  discarded — meaning adopting `Agent.run()` as-is pays roughly double the
  latency/tokens for no benefit here, and in this run the extra call
  didn't even improve accuracy (still missed the `rooms` filter). **Net
  decision: keep the raw `openai` SDK for this feature**; a plain
  Pydantic model can still be used to declare/validate the tool call
  arguments without adopting the full `Agent`/tool-execution-loop.
  Revisit full PydanticAI `Agent`s specifically for a future
  advisor/professional persona, where a genuinely *synthesized* structured
  answer (e.g. a pricing recommendation) — not a direct UI-state tool
  call — is actually what's wanted, since that's the case its two-call
  design is built for.
- **Plain Pydantic models work as the middle ground** (step 5):
  `BaseModel.model_json_schema()` produces a schema Ollama accepts as-is
  for `tools=[...]` (the extra per-property `"title"` fields Pydantic adds
  are harmless), and `model_validate_json()` cleanly parses/validates the
  returned tool-call arguments. This is the design now written into
  `contracts/tools.md` and `data-model.md`: one `BaseModel` per tool is the
  single source of truth for both the schema sent to the model and the
  validation applied to its response — still a single `openai` SDK call
  per turn, no agent/tool-execution-loop involved.
