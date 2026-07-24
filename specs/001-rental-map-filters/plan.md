# Implementation Plan: Rental Map Filters

**Branch**: `001-rental-map-filters` | **Date**: 2026-07-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-rental-map-filters/spec.md`

## Summary

Turn `main.py` into a single-page Streamlit app that loads the enriched
listings dataset, exposes sidebar filters for neighborhood and every numeric
attribute (rooms, parking spots, suites, area, price, condo fee, IPTU), and
renders the matching listings as an interactive, tooltip-enabled map
alongside a sortable results table — satisfying FR-001 through FR-016 in the
spec.

## Technical Context

**Language/Version**: Python >= 3.13 (per `.python-version` / `pyproject.toml`)

**Primary Dependencies**: `streamlit` (UI + app server, not yet added — will
add via `uv add streamlit`), `pandas` (already a dependency, data loading and
filtering), `pydeck` (map layer with tooltips; bundled with Streamlit, so no
separate dependency add expected — confirmed in research.md)

**Storage**: Flat file — `data/dados_apartamentos_with_coordinates.csv`
(~18,780 rows, `;`-separated), read-only at app runtime. No database.

**Testing**: Manual verification by running `uv run streamlit run main.py`
and exercising each acceptance scenario in `quickstart.md`, per constitution
Principle V. No automated UI test suite is in scope for this feature.

**Target Platform**: Local/dev web browser via Streamlit's built-in server.

**Project Type**: Single-page web app (Streamlit).

**Performance Goals**: Filter changes feel instant — results update well
under the 10-second interaction budget in SC-001, comfortably achievable
since ~18.8k rows is small for in-memory pandas boolean filtering.

**Constraints**: Must not mutate `data/dados_apartamentos.csv` or
`data/dados_apartamentos_with_coordinates.csv` (constitution Principle I);
new dependencies only via `uv add` (Principle II); all identifiers/file names
in English even though data/columns are Portuguese (Principle III).

**Scale/Scope**: ~18,780 listings across 145 neighborhoods; one page; 7
filter controls (1 multiselect + 6 range sliders) + map + results table.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Reproducible Data Pipeline | PASS | App only reads the existing enriched CSV; no in-place writes. No new enrichment script needed for this feature. |
| II. uv-Managed Dependencies | PASS | `streamlit` added via `uv add streamlit`; app run via `uv run streamlit run main.py`. |
| III. English-Only Code & Naming | PASS | All new functions/variables/files in English; Portuguese appears only as literal `Bairro` values and existing CSV column headers. |
| IV. Spec-Driven Feature Development | PASS | This plan follows `specify` (spec.md) and precedes `tasks`/`implement`. |
| V. Simplicity & Verify-in-Browser | PASS | Single-file app to start (see Structure Decision); `quickstart.md` defines the manual verification steps required before calling this done. |

No violations. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-rental-map-filters/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
└── tasks.md              # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` directory: this feature has no external API, CLI, or service
interface — its only interface is the Streamlit UI itself, which is fully
described by the spec's functional requirements and this plan's data model.

### Source Code (repository root)

```text
main.py                  # Streamlit app entry point: page config, data
                          # loading (cached), sidebar filters, map, table
data/
├── dados_apartamentos.csv                     # source, untouched
└── dados_apartamentos_with_coordinates.csv    # enriched input this app reads
scripts/
└── enrich_coordinates.py  # existing, unchanged by this feature
```

**Structure Decision**: Single project, single entry-point file
(`main.py`), consistent with the repo's existing scaffold and constitution
Principle V (no premature structure for an app this size). If `main.py`
grows past roughly 250-300 lines during implementation, split data
loading/filtering into a `listings.py` module — not decided upfront, since
YAGNI applies until that actually happens.

## Complexity Tracking

*No constitution violations — table not needed.*
