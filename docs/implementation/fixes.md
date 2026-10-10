# Fixes

Bugs found and how they were fixed. Newest first. Add a line for every bug fix (with a test when it's logic).

| Date | Bug | Cause | Fix |
|---|---|---|---|
| 2026-10-10 | WARNING shown on a fully cleared Daily Quest | Footer only checked Recovery vs not | Show a motivational line when every Goal is done |
| 2026-10-10 | Desktop flicker (orange top-left, green bottom, level slab, XP bar) | Animated aurora, shine and pulse effects | Removed the animations; aurora is static |
| 2026-10-10 | Level dropped after using a Recovery Potion | Potion day was evaluated as a Recovery Day (50% XP), taking back XP | Potion day evaluates as Standard, then is recorded as Recovery; no XP loss. Dev DB repaired |
| 2026-10-10 | Streak stayed 0 after clearing today | Streak only counted closed days | Count today once it's fully cleared (not on Recovery Days) |
| 2026-10-09 | Active chip text invisible on hover | Hover style overrode `.is-active` colours | `:not(:disabled, .is-active)` on chip hover |
| 2026-10-09 | Vite proxy `ECONNREFUSED`, app on :5175 | Backend not running; port drift | `run-app.py` starts both; `strictPort` on 5173 |
| 2026-10-09 | Phone can't open the dev server | Vite bound to localhost; Windows firewall | `host: true`; firewall rule still needs admin |
| 2026-10-09 | Hunter clear gave 179 XP instead of 180 | Float rounding before `floor` | `math.floor(round(x, 6))` in `engine/day.py` |
| 2026-10-09 | Notices with UUIDs failed to serialise | `model_dump()` kept UUID objects | `model_dump(mode="json")` |
| 2026-10-09 | Alembic autogenerate missed custom types | Migration template lacked the schema import | Template imports `app.repositories.db_schema` |
| 2026-10-09 | SQLAlchemy 2.1 `.tuples()` deprecation | API change | Iterate rows directly |
| 2026-10-09 | `uv run pytest` fails ("uv trampoline failed to canonicalize script path") | uv on Windows | Use `uv run python -m pytest` |
