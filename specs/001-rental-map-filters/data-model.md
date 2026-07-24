# Phase 1 Data Model: Rental Map Filters

The data model is read-only for this feature: it describes the shape of
`data/dados_apartamentos_with_coordinates.csv` as consumed by the app, not a
system the app writes to.

## Entity: Listing

One row = one apartment rental listing.

| Field | Source column | Type | Notes |
|---|---|---|---|
| Neighborhood | `Bairro` | string | Portuguese district name; used for the neighborhood filter (FR-002) and as the basis of the listing's approximate map location. Never empty (0 missing values observed). |
| Rooms | `Quartos` | integer | Filter range FR-003. |
| Parking spots | `Vagas` | integer | Filter range FR-004. |
| Suites | `Suites` | integer | Filter range FR-005. |
| Area | `Area` | integer (m²) | Filter range FR-006. |
| Price | `Valor` | float (BRL) | Monthly rental price. Filter range FR-007. |
| Condo fee | `Condominio` | float (BRL) | Filter range FR-008. |
| IPTU | `IPTU` | float (BRL) | Property tax. Filter range FR-009. |
| Latitude | `Latitude` | float, nullable | Jittered per-row around the neighborhood's geocoded point. 4 of 18,780 rows are null (neighborhood not geocoded). |
| Longitude | `Longitude` | float, nullable | Same as Latitude. |

**Validation rules**:
- A listing is included in map rendering only if both `Latitude` and
  `Longitude` are non-null (FR-015).
- A listing is included in the results table/count whenever it matches all
  active filters, regardless of coordinate presence.

**State/lifecycle**: None — the dataset is static input for the app's
lifetime; there is no create/update/delete flow. Refreshing the underlying
data means re-running `scripts/enrich_coordinates.py` and restarting the app
(out of scope for this feature, per spec Assumptions).

## Derived concept: Neighborhood

Not a separate stored entity — it's the set of distinct `Bairro` values
present in the Listing data (145 in the current dataset), used to populate
the neighborhood multiselect filter (FR-002).

## Derived concept: Active Filter Set

In-memory only, not persisted (per spec Assumptions — no cross-session
persistence required for v1):

| Filter | Applies to | Shape |
|---|---|---|
| Neighborhoods | `Neighborhood` | set of selected strings |
| Rooms range | `Rooms` | `(min, max)` inclusive |
| Parking range | `Parking spots` | `(min, max)` inclusive |
| Suites range | `Suites` | `(min, max)` inclusive |
| Area range | `Area` | `(min, max)` inclusive |
| Price range | `Price` | `(min, max)` inclusive |
| Condo fee range | `Condo fee` | `(min, max)` inclusive |
| IPTU range | `IPTU` | `(min, max)` inclusive |

A Listing matches the Active Filter Set when its Neighborhood is in the
selected set (or the set is empty/all-selected) **and** every numeric field
falls within its respective range (FR-010).
