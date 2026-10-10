# The System

Self-improvement web app modelled on the System from *Solo Leveling*: real-life habits become quests; clearing them levels you up. Personal use first, multi-user ready.

Docs live in `docs/`. Start with `docs/README.md`, which holds the decisions log and open questions. Build status, todo and the updates log are in `docs/implementation/plan.md`; bug history is in `docs/implementation/fixes.md`. Before touching game rules, read `docs/design/game-mechanics.md`. Before writing UI copy or naming anything, read `docs/design/lore-glossary.md`.

## Layout

```
backend/    FastAPI, async SQLAlchemy 2, Alembic, pytest (uv, Python 3.12)
frontend/   Vite + React 19 + TypeScript (.tsx), Tailwind v4, Motion, TanStack Query, React Router, Font Awesome (pnpm)
database/   local data files: SQLite .db, CSV/JSON exports (git-ignored, keep .gitkeep)
docs/       design, architecture, roadmap
references/ UI reference screenshots (ref1-ref8)
```

## Commands

Run the whole app. It opens two terminal windows (backend :8000, frontend :5173); Ctrl+C in the launcher, or closing either window, stops both:

```
uv run python scripts/run-app.py
```

Backend (run from `backend/`). Use `python -m`. `uv run pytest` fails here with "uv trampoline failed to canonicalize script path".

```
uv run python -m pytest                     # all tests
uv run python -m ruff check . --fix && uv run python -m ruff format .
uv run python -m mypy app                   # strict
uv run python -m alembic revision --autogenerate -m "..."   # after db_schema.py changes
uv run python -m alembic upgrade head
uv run python -m uvicorn app.main:app --reload             # :8000, docs at /docs
```

Frontend (run from `frontend/`):

```
pnpm dev        # :5173, proxies /api -> :8000 (same origin, so the session cookie works)
pnpm build      # tsc -b + vite build
pnpm lint       # oxlint
pnpm gen:api    # regenerate src/lib/api-types.ts from the running backend's OpenAPI
```

Run `pnpm gen:api` after any API model change. Then fix the type errors it surfaces.

## Backend rules

- **Layering:** `api → core → services → repositories → DB`. `engine/` holds pure game rules. `utils/` can be used from any layer.
  - `api/` routers parse input and call one `core/` flow. Every router is included from `api/router.py` only.
  - `core/` flows own the transaction (`async with uow:`) and build the `notices[]`.
  - Services never call each other. Cross-domain work goes through `core/`.
  - Only `repositories/` touch SQLAlchemy. All tables live in `repositories/db_schema.py`. Pydantic models go in `models/`. There is no `schemas/` folder.
- **Async everywhere:** use `AsyncSession` and async repos, services and flows. CPU-bound work (argon2) goes through `asyncio.to_thread`.
- **IDs:** UUID v4 everywhere. Never sort by id; use `created_at` or `sort`.
- **Time:** store UTC only (`UtcDateTime` column type). The game day comes from `utils/time.game_date(now, tz, reset_hour)`. Flows take `now` as a parameter, and tests override `get_now` to time-travel.
- **Validation:** use the `Annotated` types in `models/types.py` (`Target`, `Weekday`, `Timezone`, ...). FastAPI dependencies are `Annotated` aliases in `api/deps.py` (`Uow`, `Now`, `CurrentUser`).
- **Errors:** raise `utils/errors.py` types (`NotFound`, `Conflict`, `InvalidAction`, `Unauthorized`) with a bracketed System message, e.g. `"[This Daily Quest has ended.]"`. `main.py` maps them to `{"detail": ...}`.
- **XP is a ledger:**
  - Level, stats and gold are derived from `xp_events`, `stat_xp_events` and `gold_events`.
  - A Daily Quest's ledger rows always equal `evaluate_day` of its current progress (`core/rewards.sync_quest_rewards` writes the difference).
- **Days close lazily:** `core/day_close_flow.ensure_days_closed` runs at the start of every Player flow.
- **Tuning numbers** live in `app/config/` (`game.py`, `presets.py`, `titles.py`). Never hardcode them.
- **Mongo may come later:** keep all DB code inside `repositories/`.

## Frontend rules

- The UI never decides game outcomes. It renders what the API returns and plays `notices[]` through `NoticeQueue`.
- API calls go through `lib/api.ts` (`api` client + `call()` unwrap) and hooks in `lib/queries.ts`.
- Colours and fonts are Tailwind theme tokens in `src/index.css` (`text-system`, `text-xp`, `font-display`, ...). Look = ref2 theme, dark: `.card` panels, `.chip` (tabs/secondary, `.is-active`), `.btn` (primary), `.level-slab`, `.press` for tap feedback, `CountUp` for numbers, `buzz()` for haptics. `font-display` = Archivo. Don't add raw hex values.
- Touch targets must be at least 44px (`min-h-11`). Respect `prefers-reduced-motion`.

## Conventions

- Use the lore vocabulary in code and copy: Player, Daily Quest, Goal, Hunter Rank, Penalty Zone, Recovery Potion, Awakening. Never "task", "habit" or "achievement".
- Every new piece of logic gets a test. API tests use `tests/api/conftest.py`: in-memory SQLite plus a `clock` fixture.
- Update the docs (`overview.md` §4-5, `roadmap.md`) when the schema, the API or the roadmap status changes.
- Any rule change (XP, penalties, potions, streaks, ranks): update `docs/design/rules.md` and add a changelog line.
- After a user-visible change: add a line to `docs/implementation/plan.md` → Updates and tick/edit its Todo and phase status. After a bug fix: add a row to `docs/implementation/fixes.md`.
