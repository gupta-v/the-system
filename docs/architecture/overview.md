# Architecture Overview

Assumes stack in [../stack/tech-stack.md](../stack/tech-stack.md).

## 1. Shape

```
React PWA (frontend/)  ──HTTPS/JSON──▶  FastAPI (backend/)  ──▶  SQLite / Postgres
   UI, animation, optimistic             auth, game engine,
   updates, offline shell                day evaluation, API
```

Repo layout:

```
backend/
  app/
    api/              # FastAPI routers, one file per domain
    models/           # Pydantic models: API request/response + domain DTOs
    core/             # use-case orchestration: one entry point per user action, composes services
      daily_quest_flow.py     # log goal → update quest, award XP, check level/rank, build notices[]
      day_close_flow.py       # ensure_days_closed: evaluate missed days, penalties, streak, new Daily Quest
      onboarding_flow.py      # Awakening + Regimen interview → profile, regimen, first Daily Quest
      regimen_flow.py         # edit "this week / from now on", weekly repeat, Sunday review
      status_flow.py          # assemble Status Window (player + analytics)
      unit_of_work.py         # transaction boundary: one commit/rollback per use case
    services/         # one service per domain (business logic, calls engine + repositories)
      player_service.py       # Status Window, level/rank, stats, settings
      quest_service.py        # Daily Quest generation, logging, day evaluation, penalties
      regimen_service.py      # weekly plans, day types, overrides, repeat/edit
      notification_service.py # System notices, push, reminders
      analytics_service.py    # wraps analytics/ + figures/
      auth_service.py
      # phase 2: gate_service, dungeon_service, inventory_service, shadow_service
    repositories/     # ALL database access — no SQL/ORM calls outside this folder
      db_schema.py            # ALL SQLAlchemy table models (single source of DB schema)
      session.py              # engine, SessionLocal, get_db dependency
      user_repo.py
      quest_repo.py
      regimen_repo.py
      ledger_repo.py          # xp_events, gold_events
      # phase 2: gate_repo, inventory_repo, ...
    utils/            # shared helpers, no business rules
      time.py                 # game-date from tz + reset hour, countdowns
      security.py             # hashing, JWT/cookies
      rng.py                  # seeded RNG per (user, date)
      logging.py
    engine/           # pure game rules: xp, levels, ranks, stats, penalties (no DB, no I/O, unit-tested)
    analytics/        # pandas/NumPy/SciPy: rollups, projections, Fatigue, insights (see analytics.md)
    figures/          # Plotly figure builders + system_dark template
    jobs/             # APScheduler: Gates, Emergency Quests, reports, push
    config/           # game tuning constants, settings
  tests/
```

**No `schemas/` folder.** DB tables (SQLAlchemy) → `repositories/db_schema.py`. Pydantic models → `models/`.

### Layering rules

```
api  →  core  →  services  →  repositories  →  DB
                     │
                     └──→  engine / analytics (pure)        utils: usable by any layer
```

- `api/` only parses input (`models/`), calls **one core flow**, returns output. No DB, no game rules.
- `core/` orchestrates a use case across services (e.g. logging a Goal touches quest, player, ledger, notification). Owns the transaction (`unit_of_work`) and builds the `notices[]` returned to the UI. No direct DB access.
- `services/` hold single-domain logic. **Services don't call each other** — cross-domain work goes through `core/`. Never import SQLAlchemy directly — always go through `repositories/`.
- `repositories/` only read/write data. No game rules.
- `engine/` and `analytics/` are pure (no DB, no HTTP) → easy to test.
- `utils/` can be imported from **any layer** (api, core, services, repositories, engine). Utils themselves import nothing from the app layers — keeps them dependency-free and avoids circular imports.

### Services vs microservices

Services are **domain modules inside one FastAPI app** (modular monolith), not separate deployables. Each service talks to others only through its public functions and owns its repositories, so any of them (e.g. `notification_service` + `jobs/`, or `analytics_service`) can later be split into a standalone microservice with its own process/queue if scale needs it. For a single user, one process is simpler, cheaper and faster to build.

Frontend:

```
frontend/
  src/
    components/   # SystemWindow, QuestCard, SegmentedXPBar...
    features/     # quests, status, history, onboarding
    lib/          # api client (generated types), hooks
    styles/       # tokens
docs/
```

## 2. Game engine

Pure functions, no I/O:

- `xp_to_next(level)`, `level_from_total_xp(xp)`
- `objective_xp(objective, progress, multipliers)`
- `evaluate_day(day_log, settings) -> DayResult(completion, failed, xp_events, penalty)`
- `rank_for_level(level)`

Services call the engine and persist the resulting events via repositories.

## 3. Day lifecycle (lazy evaluation)

1. Request arrives → `core/day_close_flow.ensure_days_closed(user, now)`.
2. For each past day not yet evaluated (from `last_evaluated_day + 1` to yesterday in user tz, respecting reset hour): run `evaluate_day`, write `xp_events`, penalty quest, streak update. Mark evaluated.
3. Ensure today's `quest_day` exists → generate from active objective templates. First open of day returns `arrived: true` so UI shows `[Daily Quest has arrived.]`.

Idempotent and safe to run on every request. Background scheduler only needed later for push notifications.

## 4. Data model (as built)

Source of truth: `backend/app/repositories/db_schema.py`. All ids UUID v4, timestamps UTC. Async SQLAlchemy (aiosqlite now, Postgres later); SQLite file in repo-root `database/`.

```
users             id, email, password_hash, created_at
profiles          user_id, display_name, timezone, reset_hour, difficulty, difficulty_changed_on,
                  day_start, check_ins, equipped_title, awakened_on, last_evaluated_day,
                  sex, birth_date, height_cm, weight_kg   (Hunter profile, all optional)
user_titles       user_id, title_code (Titles defined in config/titles.py)
goals             id, user_id, name, stat, kind (check|numeric), target (A-Rank), f_target,
                  unit, scales_with_rank, weight, sets (optional taps), archived
regimens, regimen_versions (effective_from = a Monday, day_kinds json[7]), day_types, day_type_goals,
week_schedule (weekday, slot 0–1: up to 2 Routines/day)   ← regimen.md §8; day_types = Routines
daily_quests      id, user_id, day, title, day_kind, status, completion, potion_used,
                  seen_at, evaluated_at
goal_logs         id, daily_quest_id, goal_id, snapshot of name/stat/kind/target/unit/weight/sets,
                  progress, completed_at
penalty_quests    id, user_id, daily_quest_id, description, due, status (open|cleared|expired)
xp_events, stat_xp_events, gold_events
                  id, user_id, day, amount, source, ref_id   ← ledgers; level/stats/gold derived
system_notices    notices raised at day close, held until the UI fetches them
```

XP syncs live: a Daily Quest's ledger rows always equal `evaluate_day` of its current progress, so each Goal log writes only the difference. Day close finalises status, penalties and streak Titles.

Not built yet: `day_overrides`, `reminders`, `regimen_templates`, `workout_sessions`, phase 2 tables.

## 5. API (MVP, as built)

```
POST  /auth/register | /auth/login | /auth/logout      httpOnly cookie session
POST  /awakening                     onboarding + Regimen interview → first Daily Quest
GET   /me/status                     Status Window
GET   /me/rating?at=YYYY-MM-DD       level/XP/stats as of a game day ("Your Rating" tabs)
GET   /me/stats/{stat}               stat value, 30-day stat XP history, Goals feeding it
GET   /me/insights                   Rating extras: XP pace, level/rank ETA, clear rate, 84-day heatmap, records
GET   /me/xp-journey                 per-day XP (quest / penalty), gold, level-ups, potion used/earned, quest result
GET   /rules                         public: difficulty, rank, streak, potion-window rules from config (Rules scroll)
GET   /me/settings | PATCH /me/settings   incl. Hunter profile: sex, birth_date (→ age), height_cm, weight_kg
GET   /me/notices                    held System notices
GET   /days/today                    Daily Quest + countdown + arrived flag + notices
PATCH /days/today/goals/{goal_log_id}   { progress } → xp_gained, gold_gained, notices[]
POST  /days/today/clear-all
POST  /days/today/recovery-potion
GET   /days?from&to                  history for calendar
GET   /days/{day}                    one day's Daily Quest + Goals (History detail, read-only)
POST  /penalty-quests/{id}/clear
GET   /regimen | PUT /regimen        scope: this_week | from_now_on
GET/POST /goals | PATCH/DELETE /goals/{id}   (DELETE archives)
```

Mutating endpoints return `notices[]` — System messages for the UI to animate. UI never decides game outcomes. Errors: `{"detail": "[System message]"}`.

## 6. Cross-cutting

- **Time:** store UTC; compute "game date" via user tz + reset hour in one helper.
- **Security:** hashed passwords (argon2), httpOnly SameSite cookies, CORS locked to frontend origin, rate limit auth.
- **Offline (nice-to-have):** queue objective PATCHes in IndexedDB, replay on reconnect.
