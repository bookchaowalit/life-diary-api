"""What the diary refuses: missing text, unknown entry kinds, bad dates and types."""

from diary_helpers import ENTRIES, create


def test_an_entry_needs_a_title_content_and_a_date(client, owner):
    complete = {"title": "A day", "content": "Notes.", "entry_date": "2026-10-10"}
    for missing in complete:
        body = {k: v for k, v in complete.items() if k != missing}
        response = client.post(ENTRIES, headers=owner, json=body)
        assert response.status_code == 422, missing


def test_the_title_cannot_be_empty(client, owner):
    assert create(client, owner, title="").status_code == 422


def test_the_content_cannot_be_empty(client, owner):
    assert create(client, owner, content="").status_code == 422


def test_entry_type_must_be_a_known_kind(client, owner):
    assert create(client, owner, entry_type="dream").status_code == 422
    for kind in ("daily", "weekly", "monthly", "lesson", "idea", "reflection"):
        assert create(client, owner, entry_type=kind).status_code == 201, kind


def test_entry_date_must_be_a_calendar_date(client, owner):
    assert create(client, owner, entry_date="yesterday").status_code == 422
    assert create(client, owner, entry_date="2026-13-40").status_code == 422
    assert create(client, owner, entry_date="2026-10-10").status_code == 201


def test_mood_and_energy_must_be_whole_numbers(client, owner):
    assert create(client, owner, mood="happy").status_code == 422
    assert create(client, owner, energy_level=7.5).status_code == 422
    assert create(client, owner, mood=4, energy_level=7).status_code == 201


def test_an_entry_refuses_fields_it_does_not_have(client, owner):
    assert create(client, owner, weather="rain").status_code == 422


def test_required_fields_cannot_be_cleared_on_update(client, owner):
    entry = create(client, owner).json()
    path = f"{ENTRIES}/{entry['id']}"
    for field in ("title", "content", "entry_date"):
        cleared = client.patch(path, headers=owner, json={field: None})
        assert cleared.status_code == 422, field
        assert cleared.json()["detail"] == {"error": "invalid_value", "fields": [field]}
    assert client.get(path, headers=owner).json()["version"] == 1
