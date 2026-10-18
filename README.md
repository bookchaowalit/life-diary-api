# life-diary-api
The Diary (restricted) cell: its own API (Railway, serverless) and its own Neon
database, described by `cell.yaml` and served by the code in `src/cellkit/`, which
this repository owns. It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `life-diary-api`, service `diary-api` (Serverless) |
| Data | Neon project `life-diary-api`, database `diary` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`diary`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `diary.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/journal-entries` | journal-entry | `entry_type` |

## Develop and operate

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/diary-db provision
npm install && railway config apply && railway up --ci --service diary-api
railway scale --service diary-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Railway variables: `SENTRY_DSN` (error reporting; unset = off, see
`src/cellkit/_sentry.py`), `DIARY_DB_MODE=hosted`, `DIARY_DB_URL_API`,
`DIARY_JWT_PUBLIC_KEY_PEM`, `DIARY_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
