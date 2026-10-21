# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through the cell's own MCP server (`diary-mcp`, tools
  `diary.journal-entry.list|get|create|update|delete`) and the hosted tool hub
  (`platform-mcp-remote-worker`, which lists this cell's origin).
- Local owner tooling that reads cells through the registry client: `ops-toolkit`
  (`infra/scripts/utils/cell_store.py`) and `mcp-aggregator` (`src/cell-store.ts`, `EMPIRE_DIARY_API`).
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `diary.journal-entry:read|write|delete`. The cell is registered as restricted: grant these
  deliberately.
- No web page reads this cell: `life-dashboard-web` has no diary module.

## Product Purpose

A private register of journal entries (daily, weekly, monthly, lesson, idea, reflection), each with
a date, free text, optional tags, a mood and an energy level, so that reflections can be listed and
counted by kind. The markdown diary kept in the repository is not replaced by this cell.

Success: each entry the owner chooses to store exists once with its date and text, is visible only
inside the owner's workspace, and can be found again by kind.

## Positioning

One capability, one service: its own API (Railway), its own database (Neon) with row-level
security per workspace, and authorization, executions and audit through `empire-platform`. It is
workspace-scoped, so the same service can serve other tenants without code changes.

## Operating Context

- Production: `https://diary-api-production-2db8.up.railway.app` (`/health`), deployed by merging
  to `main` after CI.
- The cell was created empty on 2026-10-11: the old SQLite `journal` table held no rows, so nothing
  was imported. Imports through the API keep the old id in `legacy_id`.
- Monitored by `platform-uptime-worker` (`diary-api`); errors go to Sentry when `SENTRY_DSN` is set.
- This cell publishes no graph events (`cell.yaml` has no `graph:`).

## Capabilities and Constraints

- `/v1/journal-entries`: list (filter `entry_type`; repeat it for any-of), stats, get,
  get-by-legacy-id, create (with `Idempotency-Key`), patch (with `expected_version`), delete.
- Rules tested:
  - `title`, `content` and `entry_date` are required, `title` and `content` cannot be empty, and
    none of the three can be cleared by a patch (422 `invalid_value`).
  - `entry_type` is one of daily, weekly, monthly, lesson, idea, reflection, and is empty until given.
  - `entry_date` must be a real calendar date; `mood` and `energy_level` must be whole numbers.
  - Nothing is unique: one day can hold several entries, including with the same title.
  - Another workspace sees none of an owner's entries (404 on read and delete, empty list).
  - `stats` groups only by `entry_type`; any other `group_by` is a 422. List order is oldest
    first (`order=desc` reverses it); entries cannot be listed by date or mood.
- `mood` and `energy_level` have no range in `cell.yaml` (any 32-bit integer, including negative); a
  value above 2147483647 currently ends in a server error instead of a 422 (known gap in the shared
  service code, covered by an expected-failure test). The intended scale is [ต้องยืนยัน].
- `tags`, `related_skill_ids` and `related_asset_ids` are plain text; their format is [ต้องยืนยัน].
- Out of scope: encryption of entry text at rest beyond the database's own, search inside entries,
  and the markdown diary.

## Measures

Proposed (nothing collects them yet):

- Days with at least one entry in the last 30 days.
- Entries per `entry_type` per month (`GET /v1/journal-entries/stats?group_by=entry_type`).
- 5xx rate and p95 latency on `/v1/journal-entries` (Sentry and uptime worker).
