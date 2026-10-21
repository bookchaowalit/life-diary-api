"""Defaults of a journal entry and the rules that are NOT constraints."""

import pytest
from diary_helpers import ENTRIES, create


def test_a_new_entry_has_no_kind_mood_or_tags_until_they_are_given(client, owner):
    response = create(client, owner, title="Plain day")
    assert response.status_code == 201, response.text
    entry = response.json()
    assert entry["entry_type"] is None
    assert entry["mood"] is None
    assert entry["energy_level"] is None
    assert entry["tags"] is None
    assert entry["version"] == 1


def test_an_entry_keeps_what_was_written(client, owner):
    response = create(
        client,
        owner,
        title="Lesson",
        content="Ship small.\nReview often.",
        entry_type="lesson",
        tags="work,focus",
        mood=4,
        energy_level=6,
    )
    assert response.status_code == 201, response.text
    entry = client.get(f"{ENTRIES}/{response.json()['id']}", headers=owner).json()
    assert entry["content"] == "Ship small.\nReview often."
    assert entry["entry_type"] == "lesson"
    assert entry["tags"] == "work,focus"
    assert (entry["mood"], entry["energy_level"]) == (4, 6)
    assert entry["entry_date"] == "2026-10-10"


def test_one_day_can_hold_several_entries(client, owner):
    daily = create(client, owner, entry_type="daily")
    reflection = create(client, owner, entry_type="reflection")
    same_title = create(client, owner, entry_type="daily")
    assert {daily.status_code, reflection.status_code, same_title.status_code} == {201}
    assert (
        len({daily.json()["id"], reflection.json()["id"], same_title.json()["id"]}) == 3
    )


def test_an_entry_keeps_the_old_id_when_it_is_imported(client, owner):
    imported = create(client, owner, title="Old entry", legacy_id=777)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 777
    found = client.get(f"{ENTRIES}/legacy/777", headers=owner)
    assert found.status_code == 200
    assert found.json()["title"] == "Old entry"
    assert create(client, owner, legacy_id=777).status_code == 409


@pytest.mark.xfail(
    strict=True,
    reason="cellkit app.write does not catch NumericValueOutOfRange: a mood above "
    "2147483647 ends in a 500 instead of a 422",
)
def test_a_mood_above_the_integer_range_is_refused_not_a_server_error(client, owner):
    assert create(client, owner, mood=2**31).status_code == 422
