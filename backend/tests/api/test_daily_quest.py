from typing import Any

from httpx import AsyncClient

from tests.api.conftest import Clock


def goal(quest: dict[str, Any], name: str) -> dict[str, Any]:
    return next(g for g in quest["goals"] if g["name"] == name)


def notice_types(body: dict[str, Any]) -> list[str]:
    return [n["type"] for n in body["notices"]]


async def test_today_requires_awakening(player: AsyncClient) -> None:
    r = await player.get("/days/today")
    assert r.status_code == 409


async def test_awakening_issues_rank_scaled_training_day(player: AsyncClient) -> None:
    r = await player.post("/awakening", json={"timezone": "UTC", "extras": ["water"]})
    assert r.status_code == 200, r.text
    body = r.json()
    quest = body["quest"]
    assert quest["title"] == "Training Day"  # Monday is a default training day
    assert body["arrived"] is True
    assert notice_types(body)[:3] == ["awakening", "quest_arrived", "warning"]
    # F-Rank = 20% of the System's Daily Quest; Water is an every-day Goal, not scaled.
    assert goal(quest, "Push-ups")["target"] == 20
    assert goal(quest, "Run")["target"] == 2.0
    assert goal(quest, "Water")["target"] == 3

    again = await player.post("/awakening", json={})
    assert again.status_code == 409


async def test_second_open_is_not_an_arrival(awakened: AsyncClient) -> None:
    body = (await awakened.get("/days/today")).json()
    assert body["arrived"] is False
    assert body["notices"] == []
    assert body["seconds_until_reset"] == 19 * 3600  # 09:00 -> 04:00 next day


async def test_logging_goals_awards_xp_live(awakened: AsyncClient) -> None:
    quest = (await awakened.get("/days/today")).json()["quest"]
    pushups = goal(quest, "Push-ups")

    r = await awakened.patch(f"/days/today/goals/{pushups['id']}", json={"progress": 10})
    assert r.status_code == 200, r.text
    assert r.json()["xp_gained"] == 8  # half of a 1-of-6-Goals share (16.67), floored

    r = await awakened.patch(f"/days/today/goals/{pushups['id']}", json={"progress": 0})
    assert r.json()["xp_gained"] == -8  # lowering progress takes XP back

    status = (await awakened.get("/me/status")).json()
    assert status["total_xp"] == 0


async def test_clear_all_completes_quest_and_levels_up(awakened: AsyncClient) -> None:
    r = await awakened.post("/days/today/clear-all")
    body = r.json()
    assert body["xp_gained"] == 120  # 100 + 20% clear-all bonus
    assert body["gold_gained"] == 60
    assert notice_types(body) == ["quest_complete", "level_up"]
    assert body["quest"]["completion"] == 1.0

    status = (await awakened.get("/me/status")).json()
    assert (status["level"], status["hunter_rank"], status["gold"]) == (2, "F", 60)
    assert status["stats"]["STR"]["xp"] == 51  # 3 of 6 Goals are STR: 17 each
    assert status["stats"]["STR"]["delta"] == 1


async def test_day_close_keeps_streak(awakened: AsyncClient, clock: Clock) -> None:
    await awakened.post("/days/today/clear-all")
    clock.advance(days=1)
    today = (await awakened.get("/days/today")).json()
    assert today["quest"]["title"] == "Standard Day"
    assert today["arrived"] is True

    history = (
        await awakened.get("/days", params={"from": "2026-10-12", "to": "2026-10-13"})
    ).json()
    assert [(d["day"], d["status"]) for d in history] == [
        ("2026-10-12", "cleared"),
        ("2026-10-13", "open"),
    ]
    assert (await awakened.get("/me/status")).json()["streak"] == 1


async def test_missed_day_fails_and_issues_penalty_quest(
    awakened: AsyncClient, clock: Clock
) -> None:
    clock.advance(days=1)  # Monday closes with nothing logged
    today = (await awakened.get("/days/today")).json()
    assert "penalty" in notice_types(today)

    status = (await awakened.get("/me/status")).json()
    assert status["streak"] == 0
    [penalty] = status["penalty_quests"]
    assert penalty["description"].startswith("Survive")

    r = await awakened.post(f"/penalty-quests/{penalty['id']}/clear")
    assert r.status_code == 200
    assert (await awakened.get("/me/status")).json()["penalty_quests"] == []


async def test_long_absence_closes_every_day(awakened: AsyncClient, clock: Clock) -> None:
    clock.advance(days=10)
    await awakened.get("/days/today")
    history = (
        await awakened.get("/days", params={"from": "2026-10-12", "to": "2026-10-22"})
    ).json()
    statuses = [d["status"] for d in history]
    assert len(statuses) == 11
    assert statuses[-1] == "open"
    # Sundays (Recovery) and Standard days (no Goals) are neutral: never failed.
    assert statuses.count("recovery") == 5
    assert statuses.count("failed") == 5
    # Only yesterday's Penalty Quest is still clearable; older ones were over before we returned.
    [penalty] = (await awakened.get("/me/status")).json()["penalty_quests"]
    assert penalty["due"] == "2026-10-23T04:00:00Z"


async def earn_potion(client: AsyncClient, clock: Clock) -> None:
    """From Monday: jump to Sunday (Recovery Day), clear it, land on the next Monday."""
    clock.advance(days=6)
    r = await client.post("/days/today/clear-all")
    assert r.json()["quest"]["day_kind"] == "recovery"
    assert r.json()["notices"][0]["message"] == "[Reward: Recovery Potion acquired.]"
    clock.advance(days=1)


async def test_recovery_potion(awakened: AsyncClient, clock: Clock) -> None:
    none = await awakened.post("/days/today/recovery-potion")
    assert none.status_code == 422
    assert "Clear a Recovery Day" in none.json()["detail"]

    await earn_potion(awakened, clock)
    assert (await awakened.get("/me/status")).json()["recovery_potions"] == 1
    r = await awakened.post("/days/today/recovery-potion")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["quest"]["day_kind"] == "recovery"
    assert body["notices"][0]["data"]["potions"] == 0

    again = await awakened.post("/days/today/recovery-potion")
    assert again.status_code == 422


async def test_potion_not_on_recovery_day(awakened: AsyncClient, clock: Clock) -> None:
    await earn_potion(awakened, clock)
    clock.advance(days=6)  # next Sunday: a Recovery Day
    r = await awakened.post("/days/today/recovery-potion")
    assert r.status_code == 422
    assert r.json()["detail"] == "[Today is already a Recovery Day.]"


async def test_goal_from_closed_day_is_locked(awakened: AsyncClient, clock: Clock) -> None:
    old = (await awakened.get("/days/today")).json()["quest"]["goals"][0]
    clock.advance(days=1)
    r = await awakened.patch(f"/days/today/goals/{old['id']}", json={"progress": 1})
    assert r.status_code == 422
    assert r.json()["detail"] == "[This Daily Quest has ended.]"


async def test_negative_progress_rejected(awakened: AsyncClient) -> None:
    g = (await awakened.get("/days/today")).json()["quest"]["goals"][0]
    r = await awakened.patch(f"/days/today/goals/{g['id']}", json={"progress": -1})
    assert r.status_code == 422


async def test_streak_counts_today_once_cleared(awakened: AsyncClient) -> None:
    quest = (await awakened.get("/days/today")).json()["quest"]
    await awakened.patch(f"/days/today/goals/{quest['goals'][0]['id']}", json={"progress": 999})
    assert (await awakened.get("/me/status")).json()["streak"] == 0  # partial: not yet

    await awakened.post("/days/today/clear-all")
    assert (await awakened.get("/me/status")).json()["streak"] == 1  # cleared: counts now


async def test_get_past_day(awakened: AsyncClient, clock: Clock) -> None:
    await awakened.post("/days/today/clear-all")
    clock.advance(days=1)
    day = (await awakened.get("/days/2026-10-12")).json()
    assert (day["title"], day["status"]) == ("Training Day", "cleared")
    assert all(g["done"] for g in day["goals"])

    assert (await awakened.get("/days/2020-01-01")).status_code == 404
    assert (await awakened.get("/days/today")).status_code == 200  # literal route still wins


async def test_potion_keeps_earned_xp(awakened: AsyncClient, clock: Clock) -> None:
    await earn_potion(awakened, clock)
    quest = (await awakened.get("/days/today")).json()["quest"]
    pushups = goal(quest, "Push-ups")
    await awakened.patch(f"/days/today/goals/{pushups['id']}", json={"progress": 20})
    before = (await awakened.get("/me/status")).json()["total_xp"]

    r = await awakened.post("/days/today/recovery-potion")
    assert r.status_code == 200, r.text
    assert r.json()["xp_gained"] == 0
    assert (await awakened.get("/me/status")).json()["total_xp"] == before


async def test_potion_refused_after_clear(awakened: AsyncClient, clock: Clock) -> None:
    await earn_potion(awakened, clock)
    await awakened.post("/days/today/clear-all")
    r = await awakened.post("/days/today/recovery-potion")
    assert r.status_code == 422
    assert "already cleared" in r.json()["detail"]


async def test_standard_day_pays_flat_gold_no_xp(awakened: AsyncClient, clock: Clock) -> None:
    await awakened.patch("/me/settings", json={"difficulty": "monarch"})
    clock.advance(days=1)  # Tuesday: Standard day (Default Routine)
    body = (await awakened.post("/days/today/clear-all")).json()
    assert (body["xp_gained"], body["gold_gained"]) == (0, 5)  # same at every difficulty
    potion = await awakened.post("/days/today/recovery-potion")
    assert potion.status_code == 422
    clock.advance(days=1)
    day = (await awakened.get("/days/2026-10-13")).json()
    assert day["status"] == "recovery"  # neutral: never fails, streak kept


async def test_goal_sets_snap_progress_and_pay_partial_xp(
    awakened: AsyncClient, clock: Clock
) -> None:
    goals = {g["name"]: g["id"] for g in (await awakened.get("/goals")).json()}
    r = await awakened.patch(f"/goals/{goals['Push-ups']}", json={"sets": 4})
    assert r.json()["sets"] == 4
    r = await awakened.patch(f"/goals/{goals['Water']}", json={"sets": 4})  # 3 L in 4 sets
    clock.advance(days=2)  # Wednesday: Training Day, issued with the sets
    quest = (await awakened.get("/days/today")).json()["quest"]
    pushups, water = goal(quest, "Push-ups"), goal(quest, "Water")
    assert (pushups["sets"], pushups["target"]) == (4, 20)

    r = await awakened.patch(f"/days/today/goals/{pushups['id']}", json={"progress": 7})
    assert r.json()["quest"]["goals"][0]["progress"] == 5  # snapped to 1 of 4 sets
    r = await awakened.patch(f"/days/today/goals/{water['id']}", json={"progress": 1.5})
    logged = goal(r.json()["quest"], "Water")
    assert (logged["progress"], logged["done"]) == (1.5, False)  # 2 of 4 sets
    assert r.json()["xp_gained"] > 0  # partial XP for sets done
