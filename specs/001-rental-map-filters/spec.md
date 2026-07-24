# Feature Specification: Rental Map Filters

**Feature Branch**: `001-rental-map-filters`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Enrich apartment listings with per-neighborhood coordinates, then let a user filter listings by their attributes (neighborhood, rooms, parking spots, suites, area, price, condo fee, IPTU) and see the matching listings plotted on a map of Rio de Janeiro."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See all listings on a map (Priority: P1)

A prospective renter opens the app and sees every available rental listing
plotted as a point on a map of Rio de Janeiro, without needing to apply any
filters first.

**Why this priority**: This is the app's core value proposition — a
geographic overview of the market — and is the minimum viable product. Every
other story builds on top of this baseline view.

**Independent Test**: Open the app with no filters applied; confirm the map
renders a point for every listing in the dataset, spread across the
neighborhoods present in the data.

**Acceptance Scenarios**:

1. **Given** the app has just loaded, **When** no filters have been applied,
   **Then** the map shows one point per listing in the dataset.
2. **Given** the dataset has multiple listings in the same neighborhood,
   **When** the map is displayed, **Then** those listings appear as visually
   distinguishable points rather than a single stacked marker.

---

### User Story 2 - Filter listings by neighborhood (Priority: P2)

A renter narrows the map down to one or more specific neighborhoods they're
interested in living in.

**Why this priority**: Neighborhood is typically the primary decision factor
for renters in Rio de Janeiro and delivers immediate, high-value narrowing on
top of the P1 baseline.

**Independent Test**: Select one or more neighborhoods in the filter
controls; confirm the map and listing count only reflect listings in the
selected neighborhood(s).

**Acceptance Scenarios**:

1. **Given** the full set of listings is displayed, **When** the user selects
   a single neighborhood, **Then** only listings in that neighborhood remain
   visible on the map.
2. **Given** the full set of listings is displayed, **When** the user selects
   multiple neighborhoods, **Then** listings from all selected neighborhoods
   remain visible and listings from unselected neighborhoods are hidden.
3. **Given** a neighborhood filter is active, **When** the user clears the
   selection, **Then** listings from all neighborhoods are shown again.

---

### User Story 3 - Filter listings by numeric attributes (Priority: P3)

A renter narrows listings down by budget and space requirements: number of
rooms, parking spots, suites, area, monthly rent, condo fee, and IPTU
(property tax).

**Why this priority**: After location, budget and space are the next most
common constraints renters use to shortlist options; this is what turns a
map of "everything nearby" into a map of "things I can actually consider."

**Independent Test**: Set a range on any one numeric attribute (e.g. monthly
rent); confirm the map and listing count only reflect listings within that
range, and that this filter combines correctly with neighborhood selection
from User Story 2.

**Acceptance Scenarios**:

1. **Given** the full set of listings is displayed, **When** the user sets a
   minimum and maximum monthly rent, **Then** only listings within that range
   remain visible.
2. **Given** a neighborhood filter and a numeric filter are both active,
   **When** both are applied, **Then** only listings satisfying every active
   filter simultaneously remain visible.
3. **Given** any numeric filter is active, **When** the user resets it to its
   full range, **Then** listings outside the previous range reappear (subject
   to any other still-active filters).

---

### User Story 4 - Inspect and list matching listings (Priority: P4)

A renter looks at an individual point on the map to see its details (e.g.
neighborhood, price, area), and can also browse the full set of currently
matching listings as a list.

**Why this priority**: Complements the map with the specifics renters need
before treating a listing as a real candidate; valuable but only after
filtering (P2/P3) already narrows results down to a manageable set.

**Independent Test**: With any filter combination applied, inspect a point on
the map and confirm its key details are shown; separately, confirm a list of
the same currently-matching listings is available.

**Acceptance Scenarios**:

1. **Given** the map is displaying listings, **When** the user inspects a
   specific point, **Then** that listing's neighborhood, price, and other key
   attributes are shown.
2. **Given** any filter combination is active, **When** the user views the
   listing list, **Then** it contains exactly the listings currently shown on
   the map, no more and no fewer.

### Edge Cases

- What happens when the active filter combination matches zero listings? The
  system must show an explicit "no listings match" state rather than a blank
  or misleading map.
- What happens when a neighborhood has only one listing? It must still be
  visible and distinguishable on the map.
- What happens when a numeric filter's minimum and maximum are set to the
  same value? Only listings with that exact value should remain.
- What happens when a listing is missing coordinate data? It must be excluded
  from the map without breaking the map or filters for other listings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a map of Rio de Janeiro with one point per
  rental listing in the dataset.
- **FR-002**: System MUST allow users to filter listings by one or more
  neighborhoods.
- **FR-003**: System MUST allow users to filter listings by number of rooms,
  using a minimum/maximum range.
- **FR-004**: System MUST allow users to filter listings by number of parking
  spots, using a minimum/maximum range.
- **FR-005**: System MUST allow users to filter listings by number of
  suites, using a minimum/maximum range.
- **FR-006**: System MUST allow users to filter listings by area (m²), using
  a minimum/maximum range.
- **FR-007**: System MUST allow users to filter listings by monthly rental
  price, using a minimum/maximum range.
- **FR-008**: System MUST allow users to filter listings by condo fee, using
  a minimum/maximum range.
- **FR-009**: System MUST allow users to filter listings by IPTU (property
  tax), using a minimum/maximum range.
- **FR-010**: System MUST apply all active filters simultaneously (combined
  with AND logic), updating the map to show only listings matching every
  active filter.
- **FR-011**: System MUST display the current count of listings matching the
  active filters.
- **FR-012**: System MUST display an explicit "no listings match" message
  when the active filters match zero listings, instead of an empty map.
- **FR-013**: System MUST let users view the currently matching listings as a
  list, showing each listing's key attributes (neighborhood, rooms, parking
  spots, suites, area, price, condo fee, IPTU).
- **FR-014**: System MUST let users see a listing's key attributes by
  inspecting its point on the map (e.g. via hover or click), without
  navigating away from the map.
- **FR-015**: System MUST exclude listings without valid coordinate data from
  the map, while still including them in the filtered list view (FR-013) if
  they match the active filters.
- **FR-016**: System MUST visually distinguish listings that share the same
  neighborhood so they do not render as a single overlapping point on the
  map.

### Key Entities

- **Listing**: A single apartment rental. Attributes: neighborhood, number of
  rooms, number of parking spots, number of suites, area (m²), monthly
  rental price, condo fee, IPTU (property tax), and a map location
  (latitude/longitude).
- **Neighborhood**: A named district of Rio de Janeiro that groups listings
  and anchors their approximate map location.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from the unfiltered full listing set to a
  narrowed set filtered by neighborhood and price in under 10 seconds of
  interaction.
- **SC-002**: 100% of listings visible on the map at any time satisfy every
  currently active filter — no stale or mismatched points are ever shown.
- **SC-003**: For any point a user inspects on the map, that listing's
  neighborhood and price are visible without additional navigation.
- **SC-004**: A first-time user can reach a relevant, filtered view of
  listings within 1 minute of opening the app, without external instructions.
- **SC-005**: When a filter combination matches zero listings, 100% of the
  time the user sees an explicit message rather than an ambiguous empty
  screen.

## Assumptions

- The listing dataset is the enriched file produced by the data-enrichment
  script (neighborhood-level coordinates with small per-listing variation so
  same-neighborhood listings are visually distinguishable on the map).
- This is a single-user, single-session experience: filter selections do not
  need to persist across app restarts or be shareable between users for this
  version.
- Listings without valid coordinates (if any) are excluded from the map but
  do not block the rest of the app from functioning.
- Monthly rental price, condo fee, and IPTU values are in Brazilian Reais
  (BRL) and are displayed as provided in the dataset, with no currency
  conversion.
- No user accounts, authentication, or saved searches are required for this
  version.
- The dataset is refreshed by re-running the data-enrichment process
  (out of scope for this feature) rather than updated live within the app.
