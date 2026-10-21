# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/life-diary-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, the only tests were the generic contract suite, and an integer field (mood, energy_level) above 2147483647 ends in a server error instead of a 422.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — An entry needs a title, text and a date

- **Given** an owner with write permission
- **When** they create an entry without a title, content or entry_date, or with an empty title or content
- **Then** the API answers 422 in every case
- **Test:** `tests/test_journal_entry_validation.py::test_an_entry_needs_a_title_content_and_a_date` · level: integration (API + throwaway PostgreSQL)

### AC-02 — Required fields cannot be cleared on update

- **Given** a stored entry
- **When** a patch sets title, content or entry_date to null
- **Then** the API answers 422 `invalid_value` naming the field and the version stays 1
- **Test:** `tests/test_journal_entry_validation.py::test_required_fields_cannot_be_cleared_on_update` · level: integration (API + throwaway PostgreSQL)

### AC-03 — Entry kind, date and numbers are checked

- **Given** an entry body
- **When** `entry_type` is not one of daily, weekly, monthly, lesson, idea, reflection, `entry_date` is not a calendar date, or `mood` is not a whole number
- **Then** the API answers 422; the six valid kinds are accepted
- **Test:** `tests/test_journal_entry_validation.py::test_entry_type_must_be_a_known_kind` · level: integration (API + throwaway PostgreSQL)

### AC-04 — One day can hold several entries

- **Given** an owner
- **When** they write a daily entry, a reflection and a second daily entry with the same title for one date
- **Then** all three are created with different ids
- **Test:** `tests/test_journal_entry_defaults.py::test_one_day_can_hold_several_entries` · level: integration (API + throwaway PostgreSQL)

### AC-05 — Listing and stats follow the declared filter

- **Given** entries of several kinds
- **When** the owner lists by `entry_type`, repeats the filter, lists by date or mood, or groups stats by a non-filter field
- **Then** matching entries are listed oldest first, stats count per kind, and a non-filter field is refused with 422
- **Test:** `tests/test_journal_entry_queries.py` · level: integration (API + throwaway PostgreSQL)

### AC-06 — Another workspace cannot see an entry

- **Given** an entry written in one workspace
- **When** an owner of a different workspace reads, lists or deletes it
- **Then** read and delete answer 404 and the list is empty; the author still reads it
- **Test:** `tests/test_journal_entry_queries.py::test_another_workspace_cannot_see_an_entry` · level: integration (API + throwaway PostgreSQL)

### AC-07 — A patch bumps the version only when something changed

- **Given** an entry at version 1
- **When** the owner patches new content, then resends stored values
- **Then** the first patch gives version 2, the unchanged patch keeps the version; a stale `expected_version` answers 409
- **Test:** `tests/test_journal_entry_queries.py::test_a_patch_that_changes_nothing_keeps_the_version` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `/v1/*` (all resources) | unchanged | same routes and payloads; see README |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "55"` (measured 57.27% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_journal_entry_validation.py::test_an_entry_needs_a_title_content_and_a_date` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-02 | `tests/test_journal_entry_validation.py::test_required_fields_cannot_be_cleared_on_update` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-03 | `tests/test_journal_entry_validation.py::test_entry_type_must_be_a_known_kind` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_journal_entry_defaults.py::test_one_day_can_hold_several_entries` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_journal_entry_queries.py` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_journal_entry_queries.py::test_another_workspace_cannot_see_an_entry` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_journal_entry_queries.py::test_a_patch_that_changes_nothing_keeps_the_version` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
