from datetime import UTC, date, datetime
from uuid import uuid4

from app.utils.rng import seeded_rng
from app.utils.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.utils.time import game_date, next_reset, seconds_until_reset

TZ = "Asia/Kolkata"  # UTC+05:30


def test_game_date_before_reset_counts_as_previous_day() -> None:
    now = datetime(2026, 10, 9, 21, 0, tzinfo=UTC)  # 02:30 on Oct 10 local
    assert game_date(now, TZ, reset_hour=4) == date(2026, 10, 9)


def test_game_date_after_reset() -> None:
    now = datetime(2026, 10, 9, 23, 0, tzinfo=UTC)  # 04:30 on Oct 10 local
    assert game_date(now, TZ, reset_hour=4) == date(2026, 10, 10)


def test_next_reset_and_countdown() -> None:
    now = datetime(2026, 10, 9, 21, 0, tzinfo=UTC)
    assert next_reset(now, TZ, 4) == datetime(2026, 10, 9, 22, 30, tzinfo=UTC)
    assert seconds_until_reset(now, TZ, 4) == 90 * 60


def test_seeded_rng_is_deterministic() -> None:
    day = date(2026, 10, 9)
    a, b = uuid4(), uuid4()
    assert seeded_rng(a, day, "drop").random() == seeded_rng(a, day, "drop").random()
    assert seeded_rng(a, day, "drop").random() != seeded_rng(b, day, "drop").random()
    assert seeded_rng(a, day, "drop").random() != seeded_rng(a, day, "gate").random()


def test_password_hashing() -> None:
    h = hash_password("arise")
    assert verify_password(h, "arise")
    assert not verify_password(h, "wrong")


def test_access_token_roundtrip() -> None:
    user_id = uuid4()
    assert decode_access_token(create_access_token(user_id)) == user_id
    assert decode_access_token("garbage") is None
