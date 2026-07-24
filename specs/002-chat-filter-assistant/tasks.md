---
description: "Task list for the Chat Filter Assistant feature"
---

# Tasks: Chat Filter Assistant

**Input**: Design documents from `/specs/002-chat-filter-assistant/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/tools.md, quickstart.md

**Tests**: Not requested for this feature. Per the constitution
(Principle V), verification is manual — running the app against both
live-verified backends (Ollama, OpenRouter) and exercising
quickstart.md's scenarios.

**Organization**: Tasks are grouped by user story (spec.md priorities
P1–P4). Per plan.md's Structure Decision, this feature splits work across
two files: `main.py` (existing UI, extended) and new `chat.py` (LLM
integration). Tasks touching different files with no dependency between
them are marked `[P]`.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Add the `openai` and `pydantic` dependencies via
      `uv add openai pydantic` (updates `pyproject.toml` and `uv.lock`;
      `pydantic-ai` is deliberately NOT added — see
      `validation/README.md` for why)
- [X] T002 [P] Create `chat.py` with a `get_client()` function that reads
      `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` from `os.environ` and
      returns a configured `openai.OpenAI` client + model name, or
      `(None, None)` when `LLM_BASE_URL`/`LLM_MODEL` are unset
      (research.md #6)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The tool schemas and addressable filter widgets every story
depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 In `chat.py`, define the 3 tool argument models
      (`SetNeighborhoodsArgs`, `SetNumericRangeArgs` with its
      `FilterField` `Literal`, `ResetFiltersArgs`) as `pydantic.BaseModel`
      subclasses, an `ARG_MODELS` dict mapping tool name → model class,
      and a module-level `TOOLS` list built by calling
      `.model_json_schema()` on each model and wrapping it in the
      `{"type": "function", "function": {...}}` shape — matching
      `contracts/tools.md` exactly, including the exact-count guidance
      already written into `SetNumericRangeArgs`'s tool description
      (satisfies FR-005 structurally, no separate prompting task needed;
      depends on T002)
- [X] T004 Add a `FIELD_TO_COLUMN` mapping constant in `chat.py`
      (`rooms`→`Quartos`, `parking_spots`→`Vagas`, `suites`→`Suites`,
      `area`→`Area`, `monthly_rent`→`Valor`, `condo_fee`→`Condominio`,
      `iptu`→`IPTU`), per data-model.md (depends on T002)
- [X] T005 [P] Add the missing `key="Bairro"` to the neighborhood
      `st.multiselect` call in `main.py` — required before any
      programmatic filter update is possible (research.md #4)
- [X] T006 Initialize `st.session_state["chat_history"] = []` and
      `st.session_state["show_debug"] = False` defaults near the top of
      `main()` in `main.py` (depends on T005, same file)

**Checkpoint**: `chat.py` has a client factory and tool schemas; every
filter widget in `main.py` is addressable via `st.session_state`.

---

## Phase 3: User Story 1 - Set filters via natural language (Priority: P1) 🎯 MVP

**Goal**: A single-criterion chat message (e.g. naming just a
neighborhood) sets the corresponding filter automatically.

**Independent Test**: Type a neighborhood-only or price-only message;
confirm the matching filter control updates and results narrow
accordingly (quickstart.md scenario 1).

- [X] T007 [US1] Implement `apply_tool_call(tool_name, raw_arguments, df)`
      in `chat.py` — takes the already-loaded listings `DataFrame` as an
      explicit parameter (passed in by `main.py`'s caller, which already
      holds it via feature 001's `load_listings()`; `chat.py` must never
      import from `main.py`, since `main.py` imports `chat.py` for T010's
      wiring and that would be circular). First parses `raw_arguments`
      (the tool call's raw JSON string) via
      `ARG_MODELS[tool_name].model_validate_json(raw_arguments)`
      (T003); on `pydantic.ValidationError`, treats this tool call as not
      applied (data-model.md validation rules) and returns without
      raising. Otherwise dispatches to the 3 tools' logic using the
      validated, typed model instance, writing directly to
      `st.session_state` per data-model.md (clamp `set_numeric_range`'s
      min/max to `df[column].min()`/`.max()`; drop unrecognized
      neighborhood names from `set_neighborhoods` — checked against
      `df["Bairro"].unique()` — and track which were dropped;
      `reset_filters` deletes the relevant session-state keys). Returns a
      structured record of what was actually applied (depends on T003,
      T004)
- [X] T008 [US1] Implement `send_chat_message(client, model, user_text)`
      in `chat.py`: one `client.chat.completions.create(model=model,
      messages=[{"role": "user", "content": user_text}], tools=TOOLS,
      tool_choice="auto")` call, returning the raw response `message`
      (research.md #3; depends on T003)
- [X] T009 [US1] Add the chat UI section to `main.py`: `st.chat_input` and
      rendering of `st.session_state["chat_history"]` via
      `st.chat_message`, positioned *before* the filter-widget section in
      script order (research.md #4; depends on T006)
- [X] T010 [US1] Wire T009's input to T008 + T007 in `main.py`: on new
      chat input, call `send_chat_message`, then `apply_tool_call` for the
      returned tool call(s), before the filter widgets are instantiated
      later in the same run (depends on T007, T008, T009)

**Checkpoint**: MVP — a single-criterion chat message correctly updates
its filter and the map/table reflect it.

---

## Phase 4: User Story 2 - Combine multiple criteria in one message (Priority: P2)

**Goal**: A message naming several dimensions at once (including an exact
count like "2 bedrooms") sets all of them together.

**Independent Test**: Send a multi-criterion message; confirm all
corresponding filters are set together (quickstart.md scenario 2).

- [X] T011 [US2] Extend T010's wiring in `main.py` to apply *every* tool
      call in `message.tool_calls` (not just the first), so a response
      with multiple tool calls sets every named dimension (depends on
      T010)

**Checkpoint**: Multi-criterion and exact-count messages work end-to-end
(exact-count handling itself comes from T003's tool description, already
in place).

---

## Phase 5: User Story 3 - Get a plain-language confirmation (Priority: P3)

**Goal**: Every chat request gets a deterministic, accurate summary of
what changed, or a clear statement that nothing did.

**Independent Test**: Send a request that maps to filters, and one that
doesn't; confirm both get an appropriate reply (quickstart.md scenario 3).

- [X] T012 [US3] Implement `describe_applied_filters(applied)` in
      `chat.py`: builds a deterministic plain-language sentence from
      T007's "what was applied" records (e.g. "Set neighborhood to
      Copacabana; rent between R$500 and R$950."), or returns a fixed "no
      matching filters found" message when `applied` is empty (research.md
      #3; depends on T007)
- [X] T013 [US3] Wire T012's output into
      `st.session_state["chat_history"]` as the assistant's reply after
      each turn, rendered via `st.chat_message("assistant")` in `main.py`
      (depends on T009, T011, T012)
- [X] T014 [US3] In T007's `apply_tool_call`, track any neighborhood names
      from `set_neighborhoods` that didn't match a known `Bairro` value,
      and surface them in T012's confirmation message (spec Edge Cases;
      depends on T007, T012)

**Checkpoint**: Every chat turn — successful, partial, or empty — gets an
accurate, understandable reply.

---

## Phase 6: User Story 4 - Inspect reasoning and tool-call debug info (Priority: P4)

**Goal**: An off-by-default toggle reveals the most recently completed
turn's raw reasoning trace and raw tool-call JSON.

**Independent Test**: Toggle debug on/off around a chat message; confirm
debug data appears only when on, and only for the most recent turn
(quickstart.md scenario 4).

- [X] T015 [US4] In `chat.py`, capture `getattr(message, "reasoning",
      None)` and the raw tool-call data (name + raw JSON-string arguments,
      pre-parsing) into `st.session_state["last_debug"]` on every turn,
      overwriting the previous turn's data (research.md #2; depends on
      T008)
- [X] T016 [US4] Add a debug toggle (bound to
      `st.session_state["show_debug"]`) and, when on, render
      `last_debug`'s reasoning (or a "no reasoning trace provided by this
      backend" note when absent/empty) and raw tool-call JSON via
      `st.expander`/`st.code` in `main.py` (depends on T006, T015)

**Checkpoint**: All four user stories are independently functional and
combine correctly.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T017 Wrap T008's API call in a try/except in `chat.py`; on any
      exception, surface a clear `st.error(...)` in the chat area in
      `main.py`, apply no filter changes for that turn, and leave the rest
      of the page (manual filters, map, table) rendering normally (FR-013,
      research.md #7; depends on T008)
- [X] T018 In `main.py`, disable the chat input with a clear inline
      message when `get_client()` returns `(None, None)` (i.e.
      `LLM_BASE_URL`/`LLM_MODEL` unset), instead of erroring on first use
      (research.md #6; depends on T002, T009)
- [X] T019 Run `uv run streamlit run main.py` against both a configured
      Ollama backend and a configured OpenRouter backend, and manually
      validate all 7 scenarios in `quickstart.md`; fix any deviations
      found (constitution Principle V; depends on T001–T018). **Caveat**:
      all 7 scenarios were fully validated live against Ollama, including
      fixing a real bug found during this pass (the debug toggle's
      checkbox was defined after `st.rerun()` in the script, so it never
      re-rendered on the run that mattered — moved it before the
      chat-input processing block). OpenRouter's tool-calling was already
      independently confirmed at the API level in `validation/03` and
      `validation/05`, but a live run through the actual app was blocked
      by a safety guardrail against putting the live API key directly on
      a shell command line — deferred rather than worked around; see the
      chat transcript for details.
- [X] T020 [P] Update `README.md` with `LLM_BASE_URL`/`LLM_API_KEY`/
      `LLM_MODEL` documentation and both example configs from
      quickstart.md (no secrets included)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational only.
- **User Story 2 (Phase 4)**: Depends on User Story 1 (extends the same
  tool-call application loop built there).
- **User Story 3 (Phase 5)**: Depends on User Story 1/2 (`apply_tool_call`
  and the chat-input wiring must exist first).
- **User Story 4 (Phase 6)**: Depends on User Story 1 (`send_chat_message`
  from T008) — independent of Stories 2-3 otherwise.
- **Polish (Phase 7)**: Depends on all user stories.

### Parallel Opportunities

- T002 (`chat.py` skeleton) and T005 (`main.py` key= fix) touch different
  files with no dependency between them — genuinely parallelizable, unlike
  most of feature 001 which lived in a single file.
- T020 (README) can happen any time after the app is functional.
- Within Phase 2/3, `chat.py` tasks (T003, T004, T007, T008) are
  sequential edits to the same file, as are `main.py` tasks (T006, T009,
  T010) — not marked `[P]` even though logically distinct, to avoid
  same-file conflicts.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run the app against Ollama, confirm quickstart.md
   scenario 1
5. Demo single-criterion chat filtering if ready

### Incremental Delivery

1. Setup + Foundational → `chat.py` exists, filters are addressable
2. Add User Story 1 → single-criterion chat filtering (MVP)
3. Add User Story 2 → multi-criterion + exact-count messages
4. Add User Story 3 → plain-language confirmations, including edge cases
5. Add User Story 4 → debug toggle for troubleshooting
6. Polish → error handling, missing-config handling, dual-backend manual
   validation, README

## Notes

- [Story] label maps each task to its user story for traceability.
- Tests are intentionally not included per constitution Principle V.
- Commit after each task or logical group.
- Stop at any checkpoint to validate that story independently before
  moving on.
- Never write LLM API keys into any file in this repo — env vars only
  (see research.md #6 and quickstart.md).
