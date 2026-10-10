# The System

A self-improvement web app modelled on the System from *Solo Leveling*. Your real-life habits become
**Daily Quests**; clearing them earns XP, levels, Hunter Ranks and Gold. Miss them and you face the
**Penalty Zone**.

Personal use first, multi-user ready.

## Features

- **Daily Quest** built from your weekly plan, resetting at a set hour (default 04:00).
- **Weekly plan**: each day is Training, Standard or Recovery. Training days run up to 2
  **Routines** (sets of Goals); Standard days run the **Default Routine** (Sleep, Water).
- **Goals**: done/not-done or counted (`Push-ups × 20`), optionally split into **Sets** (tap once
  per set, hold to clear). Targets can scale with your Hunter Rank.
- **Progression**: XP ledger, levels, Hunter Ranks F → S, five stats (STR, VIT, AGI, INT, PER),
  streaks, Titles.
- **Five difficulty levels**: Awakened, Elite, National, Reawakened, Monarch. Harder means more XP
  and harsher penalties.
- **Recovery Potions**: earned on Recovery Days, used to shield a Training day.
- **History**: calendar, day detail, XP Journey. **Rating**: stats radar, rank journey, insights.
- Rules scroll, System notices, haptics, glass UI over your own background art.

## Stack

| | |
|---|---|
| Backend | Python 3.12, FastAPI, async SQLAlchemy 2 + SQLite, Alembic, Pydantic v2, pytest (uv) |
| Frontend | Vite, React 19, TypeScript, Tailwind v4, Motion, TanStack Query, React Router, Font Awesome (pnpm) |

## Getting started

Needs [uv](https://docs.astral.sh/uv/), Node 20+ and [pnpm](https://pnpm.io/).

```sh
# backend
cd backend
uv sync
uv run python -m alembic upgrade head    # creates database/the_system.db

# frontend
cd ../frontend
pnpm install
```

Run both (opens two terminal windows: API on :8000, app on :5173):

```sh
uv run python scripts/run-app.py
```

Open http://localhost:5173, create a Player and complete the Awakening. API docs: http://localhost:8000/docs.

### Background art

Images in `frontend/src/assets/art/` (`.webp`, `.png`, `.jpg`, `.svg`) are offered under
**Profile**. Add or remove files there to change the choices.

### Settings

Optional `backend/.env` (git-ignored), variables prefixed `SYSTEM_`:

| Variable | Default | |
|---|---|---|
| `SYSTEM_JWT_SECRET` | `change-me-in-env` | Set a real secret outside local dev |
| `SYSTEM_DATABASE_URL` | SQLite in `database/` | |
| `SYSTEM_COOKIE_SECURE` | `false` | `true` behind HTTPS |
| `SYSTEM_REISSUE_TODAY_ON_PLAN_EDIT` | `false` | Testing only: plan edits also rebuild today's quest |

## Development

```sh
# backend (from backend/)
uv run python -m pytest
uv run python -m ruff check . --fix && uv run python -m ruff format .
uv run python -m mypy app

# frontend (from frontend/)
pnpm build
pnpm lint
pnpm gen:api    # regenerate API types from the running backend
```

## Docs

Start at [docs/README.md](docs/README.md). Game rules: [docs/design/rules.md](docs/design/rules.md).
Build status and todo: [docs/implementation/plan.md](docs/implementation/plan.md).

## Disclaimer

Fan project inspired by *Solo Leveling*, for personal use. Not affiliated with its creators or
publishers. The background art belongs to its owners; replace it before making the repo public.
