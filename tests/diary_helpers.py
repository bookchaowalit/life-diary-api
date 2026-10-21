"""Shared helpers for the diary domain tests."""

import uuid
from typing import Any

ENTRIES = "/v1/journal-entries"


def create(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "title": "A day",
        "content": "What happened today.",
        "entry_date": "2026-10-10",
    }
    return client.post(ENTRIES, headers=owner, json={**body, **fields})


def another_workspace(harness: Any, platform: Any) -> dict[str, str]:
    """Headers of a second owner in a different workspace, with every permission."""
    actor, workspace = uuid.uuid4(), uuid.uuid4()
    platform.grants[actor] = set(harness.cell.permissions())
    headers: dict[str, str] = harness.token(actor, workspace)
    return headers
