# Quickstart: Validating the Chat Filter Assistant

## Prerequisites

- Dependencies installed, including `openai` (added via `uv add openai` as
  part of this feature's implementation).
- Feature 001's app already working (`data/dados_apartamentos_with_coordinates.csv`
  present, manual filters/map functional).
- One LLM backend configured via environment variables before launching:

  **Ollama** (confirmed working):
  ```bash
  export LLM_BASE_URL="<your Ollama endpoint>/v1"
  export LLM_API_KEY="ollama"   # placeholder, ignored by Ollama
  export LLM_MODEL="qwen3:8b"
  ```

  **OpenRouter** (confirmed working):
  ```bash
  export LLM_BASE_URL="https://openrouter.ai/api/v1"
  export LLM_API_KEY="<your OpenRouter key>"   # never commit this
  export LLM_MODEL="openai/gpt-4o-mini"
  ```

## Run the app

```bash
uv run streamlit run main.py
```

## Validation scenarios

Each maps to an acceptance scenario in `spec.md`.

1. **Single-criterion filter (User Story 1)**
   - Type: "apartments in Copacabana"
   - Expect: the `Bairro` sidebar filter shows "Copacabana" selected, map
     and table narrow accordingly, and the chat reply confirms it.
   - Type: "rent between 500 and 950"
   - Expect: the Monthly rent Min/Max inputs update to 500/950.

2. **Multi-criterion + exact count (User Story 2)**
   - Type: "2 bedroom apartment in Copacabana, rent between 500 and 950
     reais a month"
   - Expect: `Bairro` = Copacabana, Rooms Min/Max = 2/2, Monthly rent
     Min/Max = 500/950, all applied together.

3. **Plain-language confirmation (User Story 3)**
   - After any successful request, confirm the assistant's reply names the
     filters it changed.
   - Type something with no recognizable filter criteria (e.g. "hello");
     confirm the reply clearly states nothing was applied and no filters
     change.

4. **Debug view (User Story 4)**
   - With the debug toggle off, send a message; confirm no reasoning/raw
     tool-call data is visible anywhere.
   - Turn the toggle on, send another message; confirm the reasoning trace
     (if the backend provides one — Ollama/qwen3 does, OpenRouter/gpt-4o-mini
     does not) and the raw tool-call JSON for *that* message are shown.
   - Send a third message; confirm the debug panel now shows only the
     third message's data, not the second's.

5. **Reset via chat**
   - With filters active from previous steps, type "show me everything
     again" (or similar); confirm all filters clear back to defaults.

6. **Unreachable backend (FR-013)**
   - Temporarily set `LLM_BASE_URL` to an invalid address and restart the
     app, or otherwise make the backend unreachable.
   - Send a chat message; confirm a clear error appears in the chat area
     and the manual filter controls (multiselect, number inputs) still work
     normally.

7. **Unrecognized neighborhood**
   - Type a request naming a neighborhood not in the dataset (e.g. a
     misspelling); confirm the reply states it wasn't recognized rather
     than silently applying nothing or crashing.

## Done criteria

All seven scenarios behave as described, confirming this feature matches
`spec.md` before considering it complete (constitution Principle V).
