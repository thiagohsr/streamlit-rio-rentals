# Plan: Filterable Map of Rio Rentals

## Goal
Turn `main.py` into a Streamlit app that lets a user filter apartment listings by
their attributes (neighborhood, rooms, parking spots, suites, area, price,
condo fee, IPTU) and see the matching listings plotted on a map of Rio de
Janeiro.

## Data
`data/dados_apartamentos_with_coordinates.csv` (`;`-separated), columns:
`Bairro, Quartos, Vagas, Suites, Area, Valor, Condominio, IPTU, Latitude, Longitude`.
Latitude/Longitude are jittered per row around each neighborhood's geocoded
point (see `scripts/enrich_coordinates.py`), so every listing gets a distinct
marker even when several share a `Bairro`.

## Steps

1. **Add the Streamlit dependency**
   - `uv add streamlit`
   - Optionally `uv add pydeck` if `st.pydeck_chart` needs it explicitly
     (Streamlit bundles pydeck already, so confirm before adding).

2. **Data loading module**
   - Add a `load_data()` function (in `main.py` or a new `data.py`) that reads
     the CSV with `pandas.read_csv(sep=";")` and wraps it in
     `st.cache_data` so filtering doesn't re-read the file on every rerun.
   - Rename `Latitude`/`Longitude` to lowercase `lat`/`lon` if using
     `st.map`, since it expects those names.

3. **Build sidebar filters**
   - `Bairro`: `st.multiselect` populated from sorted unique values, default
     to all selected (or none selected = show all, whichever reads clearer).
   - `Quartos`, `Vagas`, `Suites`: integer range filters via `st.slider`
     using each column's observed min/max.
   - `Area`, `Valor`, `Condominio`, `IPTU`: numeric range filters via
     `st.slider` (float), also using observed min/max from the data.
   - Keep filter state in local variables; no need for `st.session_state`
     unless we later add cross-widget interactions.

4. **Apply filters to the DataFrame**
   - Chain boolean masks for each active filter and produce
     `filtered_df`.
   - Show a count of matching listings (`st.caption` or `st.metric`) so the
     user gets feedback when filters return zero rows.

5. **Render the map**
   - Start with `st.map(filtered_df, latitude="lat", longitude="lon")` for a
     quick baseline.
   - Upgrade to `st.pydeck_chart` with a `ScatterplotLayer` if we want
     tooltips (e.g. show `Bairro`, `Valor`, `Area` on hover) and per-point
     color (e.g. by price bucket).

6. **Show a results table**
   - Below the map, render `filtered_df` in `st.dataframe`, sorted by price
     by default, so users can inspect the exact listings behind the dots.

7. **Page polish**
   - `st.set_page_config(layout="wide", page_title=...)`.
   - Add a short title/description at the top.
   - Handle the empty-results case explicitly (message instead of a blank
     map/table).

8. **Manual verification**
   - Run `uv run streamlit run main.py` and check:
     - Filters narrow the map/table as expected.
     - Selecting a single `Bairro` still shows spread-out (jittered) points,
       not one stacked marker.
     - Edge cases: no `Bairro` selected, filters that yield zero rows.

## Later ideas (not in initial scope)
- Price-per-m² derived column and filter.
- Marker clustering for dense neighborhoods.
- "Reset filters" button.
- Export filtered results to CSV from the UI.
