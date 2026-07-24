# Feature Specification: Chat Filter Assistant

**Feature Branch**: `002-chat-filter-assistant`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Add a chat interface to the Rio rentals Streamlit app that lets users describe what they're looking for in natural language, and have an LLM parse that into tool calls that set the existing filter widgets. The LLM is accessed via an OpenAI-compatible chat completions API with tool/function calling, against either a self-hosted Ollama endpoint or OpenRouter. Also include a troubleshooting/debug section: a toggle that reveals the model's raw reasoning trace and the raw tool_calls JSON it returned, intended to help debug/troubleshoot agent behavior before a proper evaluation/tracing platform is set up."

## Clarifications

### Session 2026-07-16

- Q: Is supporting multiple distinct chat personas (e.g. a renter/buyer assistant vs. a professional pricing/profit advisor) in scope for this feature, or explicitly out of scope / a separate future feature? → A: Out of scope for this feature — single persona only (the renter/buyer assistant already spec'd); a future advisor/professional persona would be its own separate feature.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set filters via natural language (Priority: P1)

A user describes what they're looking for in plain language (e.g. "apartments
in Copacabana") instead of manually adjusting the neighborhood/numeric filter
controls, and the matching filter is applied automatically.

**Why this priority**: This is the entire value proposition of the feature —
without it working for at least the simplest case, there's no feature.

**Independent Test**: Type a single-criterion request (e.g. naming just a
neighborhood) into the chat; confirm the corresponding filter control updates
and the map/results narrow accordingly, with no manual interaction.

**Acceptance Scenarios**:

1. **Given** no filters are active, **When** the user asks for listings in a
   specific neighborhood via chat, **Then** the neighborhood filter is set to
   that neighborhood and results narrow accordingly.
2. **Given** no filters are active, **When** the user asks for listings
   within a specific price range via chat, **Then** the monthly rent filter
   is set to that range and results narrow accordingly.

---

### User Story 2 - Combine multiple criteria in one message (Priority: P2)

A user describes several preferences at once (e.g. neighborhood, price
range, and number of rooms together), and all of them are applied as
combined filters.

**Why this priority**: Real requests are rarely single-dimension; this is
what makes the chat meaningfully faster than manually setting each control,
but it depends on User Story 1's single-filter mechanism already working.

**Independent Test**: Send one message naming at least two different filter
dimensions; confirm both corresponding filters are set together and combine
with existing AND logic, same as if set manually.

**Acceptance Scenarios**:

1. **Given** no filters are active, **When** the user's message names a
   neighborhood and a price range together, **Then** both filters are
   applied together and results reflect both constraints.
2. **Given** the user names an exact count for a countable attribute (e.g.
   "2 bedrooms"), **When** the request is processed, **Then** the
   corresponding range filter is set with matching minimum and maximum
   (not left unfiltered).

---

### User Story 3 - Get a plain-language confirmation (Priority: P3)

After sending a chat request, the user sees a short, plain-language summary
of what filters were applied (or a clear statement that none could be
determined), so they're never left guessing what the assistant did.

**Why this priority**: Builds trust and usability on top of Stories 1-2 —
without this, users can't tell whether their request was understood
correctly without manually inspecting every filter control.

**Independent Test**: Send a chat request; confirm a reply describing the
applied filters appears. Send a request with no recognizable filter
criteria; confirm the reply clearly states nothing could be applied.

**Acceptance Scenarios**:

1. **Given** a chat request that maps to one or more filters, **When** it's
   processed, **Then** the assistant's reply states in plain language which
   filters were changed.
2. **Given** a chat request that doesn't map to any available filter
   dimension, **When** it's processed, **Then** the assistant's reply
   clearly states that no matching filters were found, and no filters
   change.

---

### User Story 4 - Inspect reasoning and tool-call debug info (Priority: P4)

A user troubleshooting unexpected chat behavior enables a debug view to see
the model's raw reasoning trace and the raw tool-call data it returned,
without needing a separate evaluation/tracing platform.

**Why this priority**: Valuable for building confidence in and debugging the
feature from Stories 1-3, but not needed for the feature to deliver its core
value to an end user.

**Independent Test**: Enable the debug toggle, send a chat message, and
confirm the reasoning trace and tool-call data for that message are shown.
Disable the toggle and confirm they're hidden.

**Acceptance Scenarios**:

1. **Given** the debug toggle is off (default), **When** any chat message is
   sent, **Then** no reasoning trace or raw tool-call data is shown.
2. **Given** the debug toggle is on, **When** a chat message is sent,
   **Then** the model's reasoning trace and the raw tool-call data for that
   message are both visible.

### Edge Cases

- What happens when a chat message doesn't map to any available filter
  dimension (e.g. asking about amenities the dataset doesn't track)? The
  assistant must say so clearly rather than silently doing nothing.
- What happens when a chat message names a neighborhood that doesn't exist
  in the dataset (typo or unknown name)? The assistant must indicate the
  neighborhood wasn't recognized rather than silently ignoring it.
- What happens when the configured LLM backend is unreachable or errors?
  The user must see a clear error in the chat, and the manual filter
  controls must remain fully usable regardless.
- What happens when a chat request's resulting filters match zero listings?
  The existing zero-match state (from the map/filters feature) applies —
  no special handling is needed beyond what already exists.
- What happens when a new chat request's filters conflict with previously
  chat- or manually-set filters? The new request's filters simply replace
  the relevant dimensions, same as re-adjusting a manual control would.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a chat interface where users can describe
  listing preferences in natural language.
- **FR-002**: System MUST translate the user's chat message into filter
  updates (neighborhood selection and/or numeric range filters) using an LLM
  tool-calling mechanism.
- **FR-003**: System MUST apply chat-derived filter updates to the same
  underlying filter state used by the manual filter controls, so chat and
  manual adjustments stay in sync and either can be used interchangeably at
  any time.
- **FR-004**: System MUST support setting multiple filter dimensions from a
  single chat message when the user's request specifies more than one.
- **FR-005**: System MUST translate a chat-specified exact value for a
  countable attribute (e.g. "2 bedrooms") into a range filter with matching
  minimum and maximum, rather than leaving that dimension unfiltered.
- **FR-006**: System MUST reply to the user after each chat request with a
  brief, plain-language summary of which filters were applied, or a clear
  statement that none could be determined.
- **FR-007**: System MUST allow users to reset previously chat-applied
  filters via chat (e.g. asking to see everything again).
- **FR-008**: System MUST handle a chat message that does not map to any
  available filter dimension by informing the user, rather than silently
  doing nothing or erroring.
- **FR-009**: System MUST support switching which LLM backend/model serves
  chat requests via fixed, deployment-time configuration (environment
  variables/config file) — no in-app UI switcher is required for this
  version.
- **FR-010**: System MUST provide a debug/troubleshooting view, off by
  default, revealing the model's raw reasoning trace and raw tool-call data
  for the most recently completed chat turn only — not the full chat
  history.
- **FR-011**: System MUST apply chat-derived filter changes to the visible
  results/map immediately and automatically, with no separate user
  confirmation step required.
- **FR-012**: System MUST continue to support all existing manual filter
  controls unchanged alongside the chat interface.
- **FR-013**: System MUST clearly indicate when the configured LLM backend
  is unreachable or errors, without crashing the app or blocking use of the
  manual filter controls.
- **FR-014**: System MUST NOT persist the chat conversation beyond the
  current app session, consistent with the rest of the app's single-session
  scope.

### Key Entities

- **Chat Turn**: One exchange in the conversation — the user's message, the
  assistant's plain-language reply, and (if any) the filter updates it
  produced.
- **Filter Update**: A structured change to one or more filter dimensions
  (the same dimensions and Active Filter Set already defined for the
  map/filters feature), derived from a Chat Turn.
- **Debug Trace**: The model's raw reasoning text and raw tool-call data for
  a Chat Turn, retained only for on-demand display when the debug toggle is
  enabled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can go from typing a natural-language request naming at
  least one neighborhood and one numeric constraint to seeing correctly
  filtered results, without touching any manual filter control.
- **SC-002**: Across a representative set of example requests covering every
  filter dimension, the correct filter is applied on the first attempt in at
  least 8 of 10 cases.
- **SC-003**: Every chat request results in a clear confirmation of what
  filters were applied, or why none were, with no request left
  unacknowledged.
- **SC-004**: Enabling the debug toggle reveals reasoning/tool-call data for
  the most recently completed turn; disabling it hides all such content,
  with zero exceptions observed during testing.
- **SC-005**: An unreachable or erroring LLM backend never prevents the user
  from continuing to use the manual filter controls.

## Assumptions

- The chat interface supplements rather than replaces the manual filter
  controls; both read and write the same shared filter state.
- At least one OpenAI-compatible, tool-calling-capable LLM backend is
  available (a self-hosted Ollama endpoint has already been confirmed
  reachable and tool-calling-capable); OpenRouter is a documented
  alternative backend using the same integration approach.
- The filter dimensions the chat interface can act on are exactly those
  already exposed by the manual filters (neighborhood, rooms, parking
  spots, suites, area, monthly rent, condo fee, IPTU) — no new dimensions.
- No authentication or user accounts are required, consistent with the rest
  of the app.
- LLM backend/model selection is a fixed, deployment-time configuration
  choice (env vars/config file) rather than something switched in the UI at
  runtime; changing it requires editing config and restarting the app.
- The debug view only ever needs to explain the most recently completed
  turn — it does not need to retain or expose reasoning/tool-call data for
  earlier turns in the same session.
- Chat-derived filter changes are trusted to apply automatically; there is
  no intermediate review/approval step between the assistant deciding a
  filter change and it taking visible effect.
- Sending chat text to the configured LLM backend (whether self-hosted or a
  third-party API) is acceptable for this project's use case; no additional
  data-handling safeguards beyond what's already true of directly using
  either service are in scope.
- This feature supports exactly one chat persona (the renter/buyer
  assistant described in User Stories 1-4); it does not need to
  distinguish user roles, switch behavior/tools per user type, or produce
  synthesized advisory output. A distinct persona for real-estate
  professionals (e.g. pricing/profit advice) is a known future direction
  but is explicitly out of scope for this feature and would be specified
  separately.
