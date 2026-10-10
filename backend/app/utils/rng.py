"""Deterministic RNG per (user, date, purpose) so rolls can't be re-rolled by refreshing."""

import hashlib
import random
from datetime import date
from uuid import UUID


def seeded_rng(user_id: UUID, day: date, purpose: str) -> random.Random:
    digest = hashlib.sha256(f"{user_id}:{day.isoformat()}:{purpose}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))
