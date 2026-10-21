"""Listing, grouping, privacy and the lifecycle of a journal entry."""

from diary_helpers import ENTRIES, another_workspace, create


def ids(response):
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["items"]]


def test_list_filters_by_entry_type(client, owner):
    daily = create(client, owner, entry_type="daily").json()
    create(client, owner, entry_type="lesson")
    listed = client.get(ENTRIES, headers=owner, params={"entry_type": "daily"})
    assert ids(listed) == [daily["id"]]


def test_a_filter_can_be_repeated_to_match_any_kind(client, owner):
    daily = create(client, owner, entry_type="daily").json()
    idea = create(client, owner, entry_type="idea").json()
    create(client, owner, entry_type="weekly")
    listed = client.get(
        ENTRIES, headers=owner, params=[("entry_type", "daily"), ("entry_type", "idea")]
    )
    assert ids(listed) == [daily["id"], idea["id"]]


def test_an_unknown_kind_in_a_filter_is_refused(client, owner):
    assert (
        client.get(ENTRIES, headers=owner, params={"entry_type": "dream"}).status_code
        == 422
    )


def test_entries_cannot_be_listed_by_date_or_mood(client, owner):
    for field in ("entry_date", "mood", "title"):
        refused = client.get(ENTRIES, headers=owner, params={field: "2026-10-10"})
        assert refused.status_code == 422, field
        assert refused.json()["detail"]["error"] == "unknown_filter"


def test_entries_are_listed_oldest_first_and_newest_first_on_request(client, owner):
    first = create(client, owner, title="First").json()
    second = create(client, owner, title="Second").json()
    assert ids(client.get(ENTRIES, headers=owner)) == [first["id"], second["id"]]
    newest = client.get(ENTRIES, headers=owner, params={"order": "desc"})
    assert ids(newest) == [second["id"], first["id"]]


def test_stats_count_entries_per_kind(client, owner):
    create(client, owner, entry_type="daily")
    create(client, owner, entry_type="daily")
    create(client, owner, entry_type="reflection")
    stats = client.get(
        f"{ENTRIES}/stats", headers=owner, params={"group_by": "entry_type"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"] == {"daily": 2, "reflection": 1}


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    for field in ("mood", "entry_date", "tags"):
        stats = client.get(
            f"{ENTRIES}/stats", headers=owner, params={"group_by": field}
        )
        assert stats.status_code == 422, field


def test_another_workspace_cannot_see_an_entry(client, owner, harness, platform):
    stranger = another_workspace(harness, platform)
    entry = create(client, owner, title="Private thoughts").json()
    assert client.get(f"{ENTRIES}/{entry['id']}", headers=stranger).status_code == 404
    assert ids(client.get(ENTRIES, headers=stranger)) == []
    assert (
        client.delete(f"{ENTRIES}/{entry['id']}", headers=stranger).status_code == 404
    )
    assert client.get(f"{ENTRIES}/{entry['id']}", headers=owner).status_code == 200


def test_editing_an_entry_bumps_the_version(client, owner):
    entry = create(client, owner).json()
    path = f"{ENTRIES}/{entry['id']}"
    edited = client.patch(
        path, headers=owner, json={"content": "Rewritten.", "mood": 5}
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["version"] == 2
    assert edited.json()["content"] == "Rewritten."
    assert edited.json()["title"] == entry["title"]


def test_a_patch_that_changes_nothing_keeps_the_version(client, owner):
    entry = create(client, owner, mood=3).json()
    path = f"{ENTRIES}/{entry['id']}"
    same = client.patch(path, headers=owner, json={"mood": 3, "title": entry["title"]})
    assert same.status_code == 200, same.text
    assert same.json()["version"] == 1
    assert same.json()["updated_at"] == entry["updated_at"]


def test_a_stale_expected_version_is_refused(client, owner):
    entry = create(client, owner).json()
    path = f"{ENTRIES}/{entry['id']}"
    assert client.patch(path, headers=owner, json={"mood": 2}).status_code == 200
    stale = client.patch(path, headers=owner, json={"mood": 3, "expected_version": 1})
    assert stale.status_code == 409
    assert stale.json()["detail"] == {"error": "version_conflict", "version": 2}


def test_a_deleted_entry_is_gone(client, owner):
    entry = create(client, owner).json()
    path = f"{ENTRIES}/{entry['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
    assert client.delete(path, headers=owner).status_code == 404
