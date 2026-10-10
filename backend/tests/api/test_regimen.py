from typing import Any

import pytest
from httpx import AsyncClient

from app.config.settings import get_settings
from tests.api.conftest import Clock


async def _goal_ids(client: AsyncClient) -> dict[str, str]:
    return {g["name"]: g["id"] for g in (await client.get("/goals")).json()}


def _all_recovery_but_monday(ids: dict[str, str], scope: str) -> dict[str, Any]:
    return {
        "day_types": [
            {"name": "Grind", "goals": [{"goal_id": ids["Push-ups"]}]},
            {"name": "Rest", "goals": []},
        ],
        "day_kinds": ["training", *["recovery"] * 6],
        "week": [["Grind"], ["Rest"], ["Rest"], ["Rest"], ["Rest"], ["Rest"], ["Rest"]],
        "scope": scope,
    }


async def test_get_regimen_from_interview(awakened: AsyncClient) -> None:
    regimen = (await awakened.get("/regimen")).json()
    assert regimen["day_kinds"] == [
        "training",
        "standard",
        "training",
        "standard",
        "training",
        "standard",
        "recovery",
    ]
    # Standard days pick no Routines (they run the Default Routine); other days get it 2nd.
    training = ["Training Day", "Default Routine"]
    assert regimen["week"] == [
        training,
        [],
        training,
        [],
        training,
        [],
        ["Recovery Day", "Default Routine"],
    ]
    assert "Standard Day" not in [r["name"] for r in regimen["day_types"]]
    default = next(r for r in regimen["day_types"] if r["name"] == "Default Routine")
    assert [g["name"] for g in default["goals"]] == ["Sleep last night", "Water"]


async def test_this_week_edit_reverts_next_week(awakened: AsyncClient, clock: Clock) -> None:
    ids = await _goal_ids(awakened)
    r = await awakened.put("/regimen", json=_all_recovery_but_monday(ids, "this_week"))
    assert r.status_code == 200, r.text

    clock.advance(days=1)  # Tuesday: edited plan
    assert (await awakened.get("/days/today")).json()["quest"]["title"] == "Rest"

    clock.advance(days=7)  # next Tuesday: original plan is back
    assert (await awakened.get("/days/today")).json()["quest"]["title"] == "Standard Day"


async def test_from_now_on_edit_sticks(awakened: AsyncClient, clock: Clock) -> None:
    ids = await _goal_ids(awakened)
    await awakened.put("/regimen", json=_all_recovery_but_monday(ids, "from_now_on"))
    clock.advance(days=8)
    assert (await awakened.get("/days/today")).json()["quest"]["title"] == "Rest"


async def test_regimen_validation(awakened: AsyncClient) -> None:
    ids = await _goal_ids(awakened)
    spec = _all_recovery_but_monday(ids, "from_now_on")
    spec["day_kinds"] = ["recovery"] * 7  # needs a non-Recovery day
    assert (await awakened.put("/regimen", json=spec)).status_code == 422

    spec = _all_recovery_but_monday(ids, "from_now_on")
    spec["week"][0] = []  # a Training day needs a Routine
    assert (await awakened.put("/regimen", json=spec)).status_code == 422

    spec = _all_recovery_but_monday(ids, "from_now_on")
    spec["day_kinds"][1] = "standard"  # Tuesday has "Rest": Standard days take no Routines
    assert (await awakened.put("/regimen", json=spec)).status_code == 422

    spec = _all_recovery_but_monday(ids, "from_now_on")
    spec["week"][0] = ["Nope"]
    assert (await awakened.put("/regimen", json=spec)).status_code == 422

    spec = _all_recovery_but_monday(ids, "from_now_on")
    spec["week"][0] = ["Grind", "Rest", "Grind"]  # max 2 per day
    assert (await awakened.put("/regimen", json=spec)).status_code == 422
    spec["week"][0] = ["Grind", "Grind"]  # no repeats
    assert (await awakened.put("/regimen", json=spec)).status_code == 422

    spec = _all_recovery_but_monday(ids, "from_now_on")
    spec["day_types"][0]["goals"] = [{"goal_id": "00000000-0000-4000-8000-000000000000"}]
    r = await awakened.put("/regimen", json=spec)
    assert r.status_code == 422
    assert "Unknown or archived Goals" in r.json()["detail"]


async def test_goal_crud(awakened: AsyncClient, clock: Clock) -> None:
    r = await awakened.post(
        "/goals",
        json={
            "name": "Cold shower",
            "stat": "PER",
            "kind": "check",
        },
    )
    assert r.status_code == 201, r.text
    goal_id = r.json()["id"]

    r = await awakened.patch(f"/goals/{goal_id}", json={"name": "Ice bath"})
    assert r.json()["name"] == "Ice bath"

    bad = await awakened.patch(f"/goals/{goal_id}", json={"target": 5})
    assert bad.status_code == 422

    # Archiving Push-ups drops it from future Daily Quests only.
    pushups = (await _goal_ids(awakened))["Push-ups"]
    assert (await awakened.delete(f"/goals/{pushups}")).status_code == 204
    clock.advance(days=2)  # Wednesday: Training Day
    names = [g["name"] for g in (await awakened.get("/days/today")).json()["quest"]["goals"]]
    assert "Push-ups" not in names
    assert "Squats" in names


async def test_goal_validation(awakened: AsyncClient) -> None:
    r = await awakened.post(
        "/goals",
        json={
            "name": "Run",
            "stat": "AGI",
            "kind": "numeric",
            "target": 5,
            "f_target": 9,
            "scales_with_rank": True,
        },
    )
    assert r.status_code == 422
    r = await awakened.post("/goals", json={"name": "", "stat": "XYZ", "kind": "numeric"})
    assert r.status_code == 422


async def test_settings_difficulty_once_per_week(awakened: AsyncClient, clock: Clock) -> None:
    r = await awakened.patch("/me/settings", json={"difficulty": "national"})
    assert r.status_code == 200
    r = await awakened.patch("/me/settings", json={"difficulty": "monarch"})
    assert r.status_code == 422
    clock.advance(days=7)
    assert (await awakened.patch("/me/settings", json={"difficulty": "monarch"})).status_code == 200

    bad_tz = await awakened.patch("/me/settings", json={"timezone": "Mars/Olympus"})
    assert bad_tz.status_code == 422
    title = await awakened.patch("/me/settings", json={"equipped_title": "streak_7"})
    assert title.status_code == 422


async def test_two_routines_merge_and_weekday_sets_kind(
    awakened: AsyncClient, clock: Clock
) -> None:
    ids = await _goal_ids(awakened)
    spec = {
        "day_types": [
            {"name": "Mobility", "goals": [{"goal_id": ids["Water"]}]},
            {"name": "Grind", "goals": [{"goal_id": ids["Push-ups"]}]},
        ],
        # Monday: Training (from day_kinds), named after Grind, Goals from both Routines.
        "day_kinds": ["training", *["recovery"] * 6],
        "week": [["Grind", "Mobility"], ["Mobility"], [], [], [], [], []],
    }
    r = await awakened.put("/regimen", json=spec)
    assert r.status_code == 200, r.text
    assert r.json()["week"][0] == ["Grind", "Mobility"]
    clock.advance(days=7)  # next Monday (today's quest was already issued)
    quest = (await awakened.get("/days/today")).json()["quest"]
    assert quest["title"] == "Grind" and quest["day_kind"] == "training"
    assert {g["name"] for g in quest["goals"]} == {"Push-ups", "Water"}


async def test_rest_day_without_routines(awakened: AsyncClient, clock: Clock) -> None:
    ids = await _goal_ids(awakened)
    spec = {
        "day_types": [{"name": "Grind", "goals": [{"goal_id": ids["Push-ups"]}]}],
        "day_kinds": [
            "training",
            "recovery",
            "standard",
            "recovery",
            "recovery",
            "recovery",
            "recovery",
        ],
        "week": [["Grind"], [], [], [], [], [], []],
    }
    assert (await awakened.put("/regimen", json=spec)).status_code == 200
    await awakened.post("/days/today/clear-all")  # Monday (quest issued before the edit)
    clock.advance(days=1)  # Tuesday: no Routines
    quest = (await awakened.get("/days/today")).json()["quest"]
    assert quest["title"] == "Rest Day"
    assert quest["day_kind"] == "recovery" and quest["goals"] == []
    clock.advance(days=1)  # Wednesday: Standard, no Routines
    quest = (await awakened.get("/days/today")).json()["quest"]
    assert quest["title"] == "Standard Day" and quest["day_kind"] == "standard"
    # Empty Standard day is neutral: the streak is kept, never raised, never broken.
    assert (await awakened.get("/me/status")).json()["streak"] == 1
    clock.advance(days=1)
    assert (await awakened.get("/me/status")).json()["streak"] == 1
    wed = (await awakened.get("/days/2026-10-14")).json()
    assert wed["status"] == "recovery"


async def test_standard_day_runs_default_routine(awakened: AsyncClient, clock: Clock) -> None:
    clock.advance(days=1)  # Tuesday: Standard day from the interview, no Routines picked
    quest = (await awakened.get("/days/today")).json()["quest"]
    assert quest["title"] == "Standard Day" and quest["day_kind"] == "standard"
    assert {g["name"] for g in quest["goals"]} == {"Sleep last night", "Water"}


async def test_plan_edit_keeps_todays_quest(
    awakened: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "reissue_today_on_plan_edit", False)  # ignore local .env
    ids = await _goal_ids(awakened)
    await awakened.put("/regimen", json=_all_recovery_but_monday(ids, "from_now_on"))
    assert (await awakened.get("/days/today")).json()["quest"]["title"] == "Training Day"


async def test_plan_edit_reissues_todays_open_quest(
    awakened: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "reissue_today_on_plan_edit", True)  # testing switch
    ids = await _goal_ids(awakened)
    quest = (await awakened.get("/days/today")).json()["quest"]  # Monday: Training Day
    pushups = next(g for g in quest["goals"] if g["name"] == "Push-ups")
    await awakened.patch(f"/days/today/goals/{pushups['id']}", json={"progress": 20})
    assert (await awakened.get("/me/status")).json()["total_xp"] > 0

    # Keep Push-ups on Monday: its progress survives the rebuild.
    spec = _all_recovery_but_monday(ids, "from_now_on")
    assert (await awakened.put("/regimen", json=spec)).status_code == 200
    quest = (await awakened.get("/days/today")).json()["quest"]
    assert quest["title"] == "Grind"
    assert [(g["name"], g["done"]) for g in quest["goals"]] == [("Push-ups", True)]

    # Monday becomes a Standard day: Default Routine, and the Push-ups XP is taken back.
    spec["day_types"].append({"name": "Default Routine", "goals": [{"goal_id": ids["Water"]}]})
    spec["day_kinds"] = ["standard", "training", *["recovery"] * 5]
    spec["week"] = [[], ["Grind"], *[["Rest"]] * 5]
    assert (await awakened.put("/regimen", json=spec)).status_code == 200
    quest = (await awakened.get("/days/today")).json()["quest"]
    assert (quest["title"], quest["day_kind"]) == ("Standard Day", "standard")
    assert [g["name"] for g in quest["goals"]] == ["Water"]
    assert (await awakened.get("/me/status")).json()["total_xp"] == 0
