# Quickstart: Validating Rental Map Filters

## Prerequisites

- Dependencies installed, including `streamlit` (added via `uv add streamlit`
  as part of this feature's implementation).
- `data/dados_apartamentos_with_coordinates.csv` present (already generated
  by `scripts/enrich_coordinates.py`).

## Run the app

```bash
uv run streamlit run main.py
```

Streamlit prints a local URL (typically `http://localhost:8501`); open it in
a browser.

## Validation scenarios

Each scenario below maps to an acceptance scenario in `spec.md`.

1. **Baseline map (User Story 1)**
   - Open the app with no filters touched.
   - Expect: a map point for every listing; listings that share a
     neighborhood appear as visually separate points, not one stacked dot.

2. **Neighborhood filter (User Story 2)**
   - Select a single neighborhood (e.g. "Copacabana") in the sidebar.
   - Expect: only Copacabana listings remain on the map and in the results
     table/count.
   - Select a second neighborhood.
   - Expect: listings from both now appear.
   - Clear the selection.
   - Expect: all listings reappear.

3. **Numeric range filters (User Story 3)**
   - Narrow the price slider to a tight range.
   - Expect: only listings within that price range remain, combined with
     any active neighborhood selection (both filters apply together).
   - Reset the price slider to its full range.
   - Expect: previously hidden listings reappear (subject to other active
     filters).

4. **Inspect a listing / results list (User Story 4)**
   - With any filter combination active, hover/click a map point.
   - Expect: a tooltip shows that listing's neighborhood, price, and other
     key attributes.
   - Check the results table below the map.
   - Expect: it lists exactly the listings currently shown on the map.

5. **Zero-match edge case**
   - Set filters to a combination with no matches (e.g. an implausibly high
     minimum price).
   - Expect: an explicit "no listings match" message, not a blank map.

6. **Missing-coordinate rows**
   - (Optional, needs dataset inspection) Confirm the 4 rows with null
     `Latitude`/`Longitude` never appear on the map but do appear in the
     results table/count when their other attributes match active filters.

## Done criteria

All six scenarios behave as described above, confirming this feature
matches `spec.md` before considering it complete (constitution Principle V).
