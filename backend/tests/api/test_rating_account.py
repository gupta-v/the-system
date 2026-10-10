from httpx import AsyncClient

from tests.api.conftest import Clock


async def test_rating_snapshots(awakened: AsyncClient, clock: Clock) -> None:
    await awakened.post("/days/today/clear-all")  # Monday: +120 XP, level 2
    clock.advance(days=1)

    day1 = (await awakened.get("/me/rating", params={"at": "2026-10-12"})).json()
    assert (day1["level"], day1["total_xp"]) == (2, 120)
    assert day1["stats"]["STR"] == 11  # 60 STR XP -> 10 + 1

    current = (await awakened.get("/me/rating")).json()
    assert current["day"] == "2026-10-13"
    assert current["total_xp"] == 120


async def test_rating_out_of_range(awakened: AsyncClient) -> None:
    r = await awakened.get("/me/rating", params={"at": "2020-01-01"})
    assert r.status_code == 422
    r = await awakened.get("/me/rating", params={"at": "2099-01-01"})
    assert r.status_code == 422


async def test_stat_detail(awakened: AsyncClient) -> None:
    await awakened.post("/days/today/clear-all")
    detail = (await awakened.get("/me/stats/STR")).json()
    assert detail["value"] == 11
    assert len(detail["history"]) == 30
    assert detail["history"][-1] == {"day": "2026-10-12", "xp": 51}  # 3 of 6 Goals: 17 each
    names = {g["name"]: (g["done_days"], g["total_days"]) for g in detail["goals"]}
    assert names == {"Push-ups": (1, 1), "Sit-ups": (1, 1), "Squats": (1, 1)}

    assert (await awakened.get("/me/stats/XYZ")).status_code == 422


async def test_account_fields(player: AsyncClient) -> None:
    r = await player.patch(
        "/me/settings",
        json={
            "display_name": "Sung Jinwoo",
            "sex": "male",
            "birth_date": "2000-03-15",
            "height_cm": 180,
            "weight_kg": 72.5,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["display_name"] == "Sung Jinwoo"
    assert (body["sex"], body["height_cm"], body["weight_kg"]) == ("male", 180, 72.5)
    assert isinstance(body["age"], int) and body["age"] >= 26

    cleared = (await player.patch("/me/settings", json={"weight_kg": None})).json()
    assert cleared["weight_kg"] is None
    assert cleared["height_cm"] == 180  # untouched


async def test_account_validation(player: AsyncClient) -> None:
    for bad in (
        {"height_cm": 10},
        {"weight_kg": 9000},
        {"sex": "robot"},
        {"birth_date": "2099-01-01"},
    ):
        assert (await player.patch("/me/settings", json=bad)).status_code == 422, bad


async def test_xp_journey(awakened: AsyncClient, clock: Clock) -> None:
    await awakened.post("/days/today/clear-all")  # Monday: +120, level 1 -> 2
    clock.advance(days=2)  # Tuesday: Standard day, no Goals; now Wednesday
    days = (await awakened.get("/me/xp-journey")).json()["days"]
    assert [d["day"] for d in days] == ["2026-10-12", "2026-10-13", "2026-10-14"]
    assert [(d["xp"], d["total_xp"], d["level"], d["level_up"]) for d in days] == [
        (120, 120, 2, True),
        (0, 120, 2, False),
        (0, 120, 2, False),
    ]
    monday, tuesday, today = days
    assert (monday["quest_title"], monday["status"], monday["gold"]) == (
        "Training Day",
        "cleared",
        60,
    )
    assert tuesday["status"] == "recovery"
    assert today["status"] is None  # today not opened yet: no Daily Quest issued


async def test_xp_journey_shows_penalty_and_potion(awakened: AsyncClient, clock: Clock) -> None:
    await awakened.patch("/me/settings", json={"difficulty": "monarch"})
    await awakened.post("/days/today/clear-all")  # Mon 12th: XP to lose later
    clock.advance(days=6)
    await awakened.post("/days/today/clear-all")  # Sun 18th: Recovery Day cleared -> Potion
    clock.advance(days=1)
    await awakened.post("/days/today/recovery-potion")  # Mon 19th: Potion used
    clock.advance(days=3)  # Tue 20th Standard (neutral), Wed 21st missed -> fail + XP loss; now Thu
    days = {d["day"]: d for d in (await awakened.get("/me/xp-journey")).json()["days"]}
    assert days["2026-10-19"]["potion_used"] is True
    assert days["2026-10-19"]["status"] == "recovery"
    wed = days["2026-10-21"]
    assert wed["status"] == "failed"
    assert wed["xp_penalty"] < 0 and wed["xp"] == wed["xp_penalty"]


async def test_rules(client: AsyncClient) -> None:
    rules = (await client.get("/rules")).json()  # public, no login
    assert rules["base_daily_xp"] == 100
    names = [d["difficulty"] for d in rules["difficulties"]]
    assert names == ["awakened", "elite", "national", "reawakened", "monarch"]
    assert rules["ranks"][0] == {
        "rank": "F",
        "min_level": 1,
        "max_level": 4,
        "clears_per_level": 1,
        "xp_per_level": 100,
        "intensity": 0.2,
    }
    assert rules["streaks"][0]["days"] == 7


async def test_insights(awakened, clock) -> None:
    await awakened.post("/days/today/clear-all")  # Monday: +120, level 2
    r = await awakened.get("/me/insights")
    assert r.status_code == 200
    body = r.json()
    assert body["xp_per_day"] == 120
    assert body["next_rank"] == "E" and body["next_rank_level"] == 5
    assert body["xp_to_next_rank"] == 400 - 120  # level 5 needs 4 x 100 XP at F
    assert body["next_rank_eta_days"] == 3
    assert body["current_streak"] == 1 and body["best_streak"] == 1
    assert body["goals_done"] > 0 and body["days_awakened"] == 1
    assert len(body["heatmap"]) == 84 and body["heatmap"][-1]["status"] == "open"
    assert body["best_day_xp"] == 120
