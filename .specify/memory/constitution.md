<!--
Sync Impact Report
- Version change: (none) → 1.0.0 (initial ratification)
- Modified principles: n/a (first version)
- Added sections:
  - Core Principles: I. Reproducible Data Pipeline, II. uv-Managed Dependencies,
    III. English-Only Code & Naming, IV. Spec-Driven Feature Development,
    V. Simplicity & Verify-in-Browser
  - Technology Constraints
  - Development Workflow
  - Governance
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no change needed (Constitution Check
    section is generic and reads gates from this file at plan time)
  - .specify/templates/spec-template.md ✅ no change needed (no
    constitution-specific placeholders)
  - .specify/templates/tasks-template.md ✅ no change needed (task
    categorization is already generic)
  - .claude/skills/speckit-*/SKILL.md ✅ no agent-specific references requiring
    updates
- Follow-up TODOs: none
-->

# Streamlit Rio Rentals Constitution

## Core Principles

### I. Reproducible Data Pipeline (NON-NEGOTIABLE)
Source data files under `data/` (e.g. `dados_apartamentos.csv`) are treated as
immutable inputs and MUST NOT be edited or overwritten in place. Any
enrichment or transformation (geocoding, cleaning, derived columns) MUST be
implemented as a script under `scripts/` that reads the source file and
writes a new, distinctly named output file. Scripts that introduce randomness
(e.g. coordinate jitter) MUST seed it explicitly so re-running a script
reproduces the same output.
Rationale: the raw scrape/export is the single source of truth; treating it
as read-only lets any derived dataset be regenerated or audited without risk
of silently corrupting the original.

### II. uv-Managed Dependencies
All Python dependencies are declared in `pyproject.toml` and locked in
`uv.lock`, managed exclusively through `uv add` / `uv remove` (or direct,
deliberate edits to `pyproject.toml` followed by `uv lock`). Manual
`pip install`, ad hoc `requirements.txt` files, or undeclared imports MUST NOT
be used. All commands that run project code MUST go through `uv run`.
Rationale: keeps the environment reproducible for every contributor and
agent working in this repo without a second dependency-tracking mechanism.

### III. English-Only Code & Naming
Even though the source data and domain vocabulary (bairro, valor, etc.) are
in Portuguese, all code identifiers, function/variable names, file names,
comments, and commit messages MUST be written in English. Portuguese terms
may appear only as literal data values or where they are the CSV's actual
column headers.
Rationale: established project convention; keeps the codebase consistent and
accessible regardless of contributors' native language.

### IV. Spec-Driven Feature Development
Non-trivial features (anything beyond a one-line fix or config tweak) MUST
go through the spec-kit flow before implementation: `/speckit-specify` to
capture intent and scope, `/speckit-plan` to define the technical approach,
and `/speckit-tasks` to break it into actionable steps, before
`/speckit-implement` (or equivalent manual implementation) begins.
Rationale: keeps intent and design decisions documented and reviewable
instead of being implicit in code, especially important since this project
is driven heavily by AI-assisted implementation.

### V. Simplicity & Verify-in-Browser
Favor the simplest implementation that satisfies the current spec (YAGNI) —
no speculative abstractions, config layers, or feature flags for
hypothetical future needs. Since this project is a Streamlit UI, no
UI-affecting change is considered done until it has been run with
`uv run streamlit run main.py` (or equivalent) and manually exercised,
covering both the golden path and obvious edge cases (e.g. filters that
produce zero results).
Rationale: automated test coverage for Streamlit UI is limited in value here;
actually running the app is the highest-signal verification available.

## Technology Constraints
- Python >= 3.13, managed via `uv` and pinned in `.python-version`.
- Core stack: `streamlit` (UI), `pandas` (data handling), `geopy` (geocoding,
  used offline by enrichment scripts, not at app runtime).
- Data lives under `data/`; one-off/repeatable data-prep scripts live under
  `scripts/`; the Streamlit app entry point is `main.py`.

## Development Workflow
- Planning documents and spec-kit artifacts live under `docs/` and
  `.specify/` respectively; keep them in sync with what's actually built.
- Prefer small, reviewable changes; a new script or feature should note in
  its own docstring/README what it does and does not do, without duplicating
  what the spec already states.
- Before marking a feature complete, confirm: dependencies were added via
  `uv add`, source data was not mutated, naming is English-only, and the app
  was manually verified in the browser.

## Governance
This constitution supersedes ad hoc practice for this repository. Amendments
are made by editing `.specify/memory/constitution.md` via the
`/speckit-constitution` flow, which MUST update the version per semantic
versioning (MAJOR: incompatible principle removal/redefinition; MINOR: new
principle or materially expanded guidance; PATCH: clarification/wording) and
record a Sync Impact Report at the top of the file. Every `/speckit-plan` run
MUST include a Constitution Check confirming the plan does not violate these
principles, or explicitly justifying any deviation.

**Version**: 1.0.0 | **Ratified**: 2026-07-15 | **Last Amended**: 2026-07-15
