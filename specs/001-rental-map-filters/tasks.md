---
description: "Task list for the Rental Map Filters feature"
---

# Tasks: Rental Map Filters

**Input**: Design documents from `/specs/001-rental-map-filters/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Not requested for this feature. Per the constitution (Principle V),
verification is manual — running the app and exercising quickstart.md's
scenarios — rather than an automated test suite.

**Organization**: Tasks are grouped by user story (spec.md priorities
P1–P4) so each story is independently testable. Per plan.md's Structure
Decision, this feature lives entirely in `main.py` (single-file app), so
most tasks touch that one file — parallel markers are used sparingly and
only where a task genuinely touches a different file.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: Get the project able to run a Streamlit app at all.

- [X] T001 Add the `streamlit` dependency via `uv add streamlit` (updates
      `pyproject.toml` and `uv.lock`; confirms `pydeck` arrives transitively
      per research.md #1)
- [X] T002 Replace the `main()` stub in `main.py` with a Streamlit page
      skeleton: `st.set_page_config(layout="wide", page_title=...)` and a
      page title/short description (no data/filters/map yet)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared data loading that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implement a cached `load_listings()` function in `main.py` that
      reads `data/dados_apartamentos_with_coordinates.csv` with
      `pandas.read_csv(sep=";")`, decorated with `st.cache_data`
      (data-model.md Listing fields; research.md #3)
- [X] T004 Wire `load_listings()` into `main()` and render the total
      listing count via `st.caption` as a placeholder (depends on T002, T003)

**Checkpoint**: App runs, loads data, shows a count. No map or filters yet.

---

## Phase 3: User Story 1 - See all listings on a map (Priority: P1) 🎯 MVP

**Goal**: Every listing in the dataset appears as a point on a map of Rio de
Janeiro, with no filters applied.

**Independent Test**: Run the app with no filter interaction; confirm a map
point exists for every listing, and that same-neighborhood listings render
as visually separate points (quickstart.md scenario 1).

- [X] T005 [US1] Implement `render_map(df)` in `main.py` using
      `st.pydeck_chart` with a `pydeck.Layer("ScatterplotLayer", ...)`,
      plotting only rows with non-null `Latitude`/`Longitude`
      (FR-001, FR-015, FR-016; research.md #1, #6, #7)
- [X] T006 [US1] Call `render_map()` from `main()` with the full loaded
      dataset, replacing the placeholder count-only view from T004
      (depends on T004, T005)

**Checkpoint**: Baseline map is live and independently demoable — this is
the MVP.

---

## Phase 4: User Story 2 - Filter listings by neighborhood (Priority: P2)

**Goal**: Users can narrow the map down to one or more chosen neighborhoods.

**Independent Test**: Select one, then multiple, then clear neighborhoods in
the sidebar; confirm the map and count update accordingly (quickstart.md
scenario 2).

- [X] T007 [US2] Implement a neighborhood `st.multiselect` sidebar filter in
      `main.py`, options = sorted unique `Bairro` values, default = all
      (FR-002; research.md #2)
- [X] T008 [US2] Build `filtered_df` by applying the neighborhood selection
      (all listings shown when nothing is selected) and pass it to
      `render_map()` instead of the full dataset (FR-002 acceptance
      scenarios; depends on T006, T007)
- [X] T009 [US2] Update the listing count from T004 to reflect `filtered_df`
      instead of the full dataset (FR-011; depends on T008)

**Checkpoint**: Neighborhood filtering works end-to-end, independently of
later numeric filters.

---

## Phase 5: User Story 3 - Filter listings by numeric attributes (Priority: P3)

**Goal**: Users can narrow listings by rooms, parking spots, suites, area,
price, condo fee, and IPTU, combined with the neighborhood filter.

**Independent Test**: Set a price range and confirm results narrow
accordingly and combine correctly with an active neighborhood filter
(quickstart.md scenario 3).

- [X] T010 [US3] Implement paired Min/Max `st.number_input` range filters for
      rooms, parking spots, and suites in `main.py`'s sidebar, bounds from
      the dataset (FR-003, FR-004, FR-005; research.md #2 — revised from
      sliders to number inputs after manual testing showed sliders can't
      express precise ranges on wide/outlier-skewed columns)
- [X] T011 [US3] Implement paired Min/Max `st.number_input` range filters for
      area, price, condo fee, and IPTU in `main.py`'s sidebar, bounds from
      the dataset (FR-006, FR-007, FR-008, FR-009; research.md #2)
- [X] T012 [US3] Extend `filtered_df` (T008) to AND all range filters from
      T010/T011 together with the neighborhood filter into one combined mask
      (FR-010; depends on T008, T010, T011)
- [X] T013 [US3] Add a zero-match state: when `filtered_df` is empty, render
      `st.info("No listings match the selected filters.")` instead of the
      map (FR-012, SC-005; research.md #4; depends on T012)

**Checkpoint**: All filters from spec.md work together; zero-match state is
handled explicitly.

---

## Phase 6: User Story 4 - Inspect and list matching listings (Priority: P4)

**Goal**: Users can see a listing's details from the map and browse all
currently matching listings as a table.

**Independent Test**: Hover/click a map point and confirm its details show;
confirm the results table matches what's on the map (quickstart.md
scenario 4).

- [X] T014 [US4] Add `pickable=True` and a tooltip (neighborhood, price,
      rooms, area) to the `ScatterplotLayer` built in T005 (FR-014;
      research.md #1; depends on T005)
- [X] T015 [US4] Implement a results table below the map via
      `st.dataframe(filtered_df.sort_values("Valor"))` (FR-013; research.md
      #5; depends on T012)

**Checkpoint**: All four user stories are independently functional and
combine correctly.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T016 Run `uv run streamlit run main.py` and manually validate all 6
      scenarios in `quickstart.md`, including the missing-coordinate rows
      check; fix any deviations found (constitution Principle V; depends on
      T001–T015)
- [X] T017 [P] Update `README.md` with instructions to run the app
      (`uv run streamlit run main.py`) — currently empty

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational only.
- **User Story 2 (Phase 4)**: Depends on User Story 1 (extends the same
  `filtered_df`/`render_map()` built there) — not independent at the code
  level, but independently testable once built.
- **User Story 3 (Phase 5)**: Depends on User Story 2 (extends
  `filtered_df` further).
- **User Story 4 (Phase 6)**: Depends on User Story 1 (T005, for the
  tooltip) and User Story 3 (T012, for the final `filtered_df`).
- **Polish (Phase 7)**: Depends on all user stories.

### Why story phases aren't file-parallel here

Every story after US1 extends the same `filtered_df` construction and the
same `render_map()` call in `main.py` (per plan.md's single-file structure
decision), so stories are implemented sequentially in priority order rather
than by separate people on separate files. Each phase is still an
independently *testable* increment — you can stop after any checkpoint and
have a working, demoable app.

### Parallel Opportunities

- T017 (README update) can happen any time after the app is functional —
  it touches a different file and has no code dependency.
- No other meaningful cross-task parallelism exists given the single-file
  structure; this is intentional per constitution Principle V (no premature
  structural split for an app this size).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run the app, confirm quickstart.md scenario 1
5. Demo the baseline map if ready

### Incremental Delivery

1. Setup + Foundational → app loads data and shows a count
2. Add User Story 1 → baseline map (MVP)
3. Add User Story 2 → neighborhood filtering
4. Add User Story 3 → full numeric filtering + zero-match state
5. Add User Story 4 → tooltips + results table
6. Polish → manual full-scenario validation, README

## Notes

- [Story] label maps each task to its user story for traceability.
- Tests are intentionally not included per constitution Principle V.
- Commit after each task or logical group.
- Stop at any checkpoint to validate that story independently before moving
  on.
