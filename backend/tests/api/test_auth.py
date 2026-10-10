from httpx import AsyncClient


async def test_register_sets_session_cookie(player: AsyncClient) -> None:
    assert "system_session" in player.cookies
    r = await player.get("/me/settings")
    assert r.status_code == 200
    assert r.json()["display_name"] == "jinwoo"


async def test_duplicate_register_conflicts(player: AsyncClient) -> None:
    r = await player.post(
        "/auth/register", json={"email": "JINWOO@example.com", "password": "another-pass"}
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "[This Hunter is already registered.]"


async def test_login_and_logout(player: AsyncClient) -> None:
    await player.post("/auth/logout")
    player.cookies.clear()
    assert (await player.get("/me/status")).status_code == 401

    bad = await player.post(
        "/auth/login", json={"email": "jinwoo@example.com", "password": "wrong-password"}
    )
    assert bad.status_code == 401

    ok = await player.post(
        "/auth/login", json={"email": "jinwoo@example.com", "password": "arise-arise"}
    )
    assert ok.status_code == 200
    assert ok.json()["awakened"] is False
    assert (await player.get("/me/settings")).status_code == 200


async def test_validation_errors(client: AsyncClient) -> None:
    r = await client.post("/auth/register", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422


async def test_requires_login(client: AsyncClient) -> None:
    r = await client.get("/days/today")
    assert r.status_code == 401
    assert r.json()["detail"] == "[Not logged in.]"
