# Phase 0 Research: Rental Map Filters

All items below were resolvable from the existing codebase, the ratified
constitution, and verified library behavior — no `[NEEDS CLARIFICATION]`
markers remain.

## 1. Map rendering approach

- **Decision**: Render listings with `st.pydeck_chart`, using a `pydeck`
  `ScatterplotLayer` configured `pickable=True` with a tooltip showing
  neighborhood, price, rooms, and area.
- **Rationale**: FR-014 requires that a user can inspect a listing's key
  attributes directly on the map (hover/click) without navigating away.
  `st.map` plots points but does not support per-point tooltips; `pydeck`
  does, and it ships as a transitive dependency of `streamlit` (verified:
  `streamlit==1.59.2` pulls in `pydeck==0.9.3`), so no extra dependency is
  needed beyond `streamlit` itself.
- **Alternatives considered**: `st.map` — simpler call, but rejected because
  it cannot satisfy FR-014 (no tooltip/inspection support).

## 2. Filter widget types

- **Decision (revised post-implementation)**:
  - Neighborhood (FR-002): `st.multiselect`, options = sorted unique
    `Bairro` values, default = all selected.
  - Rooms, parking spots, suites, area, price, condo fee, IPTU
    (FR-003–009): paired `st.number_input` (Min/Max) per field, bounds
    taken from the dataset's observed min/max per column.
- **Rationale**: `st.slider` with the dataset's raw min/max was tried
  first (see original rationale below) but manual testing showed it fails
  for the several columns with extreme outliers (e.g. `Valor` ranges
  100–4,500,000): a single pixel of drag can represent thousands of reais,
  making it impossible to select common, realistic ranges (e.g.
  "500–950/month"). A quantile-based `st.select_slider` was tried next
  (dense stops where most listings live, sparse near outliers) but is
  still fundamentally a discrete/stepped control — any range that falls
  inside one step (e.g. 500–950, both within the first 5% bucket) remains
  unselectable. Paired `st.number_input` is the only option offering
  truly arbitrary precision, which is what the reported UX problem
  actually required. `format` is numeric-only per Streamlit's API (no
  "R$" prefix in-widget), so the currency unit lives in the field label
  instead (e.g. "Monthly rent (R$)").
- **Alternatives considered (original)**: `st.slider` — simplest widget,
  but coarse precision on wide/outlier-skewed ranges; rejected after
  real usage. `st.select_slider` with quantile breakpoints — better than
  a linear slider but still discrete; rejected because it cannot express
  arbitrary in-between values, which was the actual requirement.

## 3. Data loading & caching

- **Decision**: A single `load_listings()` function reads
  `data/dados_apartamentos_with_coordinates.csv` with
  `pandas.read_csv(sep=";")`, decorated with `st.cache_data` so the ~18.8k
  row file is parsed once per process rather than on every filter
  interaction (Streamlit reruns the whole script on each widget change).
- **Rationale**: Keeps filter interactions well within the SC-001 (<10s)
  budget without introducing a database or external cache.
- **Alternatives considered**: `st.cache_resource` — wrong semantics (meant
  for non-serializable shared objects, e.g. connections, not data);
  no caching — rejected, would re-parse the CSV on every widget change.

## 4. Empty-result and match-count handling

- **Decision**: Compute `len(filtered_df)` and show it via `st.caption`
  (e.g. "N listings match"). When `N == 0`, render an `st.info` message in
  place of the map and table instead of an empty map (FR-012).
- **Rationale**: Directly satisfies FR-011/FR-012 and SC-005 (explicit
  "no listings match" state).
- **Alternatives considered**: Always rendering an empty map — rejected,
  spec explicitly disallows an ambiguous blank/empty map.

## 5. Results list view

- **Decision**: `st.dataframe(filtered_df)` below the map, sorted by
  `Valor` (price) ascending by default, showing all listing columns.
- **Rationale**: Satisfies FR-013; `st.dataframe` supports in-browser
  sorting/scrolling for however many rows match, unlike static `st.table`.
- **Alternatives considered**: `st.table` — rejected, no sorting/scrolling
  for larger result sets.

## 6. Listings with missing coordinates

- **Decision**: Rows with `NaN` `Latitude`/`Longitude` (4 of 18,780 in the
  current dataset) are excluded from the `pydeck` layer's input but remain
  in the filtered `DataFrame` used for the results table and match count.
- **Rationale**: Directly satisfies FR-015 and the corresponding edge case
  in the spec — a listing missing coordinates shouldn't break the map, but
  shouldn't silently disappear from the app either.
- **Alternatives considered**: Dropping such rows entirely — rejected, spec
  requires they remain listable.

## 7. Same-neighborhood marker separation (FR-016)

- **Decision**: No new work needed here — `data/dados_apartamentos_with_coordinates.csv`
  already stores per-row jittered coordinates (see `scripts/enrich_coordinates.py`,
  ±0.0045° per axis, seeded), so listings sharing a `Bairro` already render as
  visually distinct points.
- **Rationale**: Confirms the existing enrichment output satisfies FR-016
  without additional client-side jitter logic in the app itself.
- **Alternatives considered**: Jittering at render time in `main.py` —
  rejected as redundant, the data already carries per-row variation.
