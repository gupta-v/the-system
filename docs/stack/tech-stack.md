# Tech Stack

Status: **proposed** — confirm before scaffolding.

## Recommendation: Python API + React frontend

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | **FastAPI** (Python 3.12+) | Python-first as requested, typed, fast, auto OpenAPI docs |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Standard, works with SQLite and Postgres |
| Validation | Pydantic v2 | Built into FastAPI |
| DB | SQLite (personal phase) → PostgreSQL (public) | Zero-ops now, same models later |
| Auth | Email + password, JWT in httpOnly cookie (fastapi-users or hand-rolled) | Single user now, multi-user ready |
| Tests | pytest | Game rules (XP, penalties) must be unit-tested |
| Frontend | **React + Vite + TypeScript** | Motion-heavy UI needs a real component framework |
| Styling | Tailwind CSS v4 + CSS variables for tokens | Fast, responsive utilities |
| Animation | Motion (Framer Motion) | Layout animations, sequenced System windows |
| Data fetching | TanStack Query | Caching, optimistic checkbox updates |
| Routing | React Router | |
| PWA | vite-plugin-pwa | Installable, offline shell |
| API types | openapi-typescript generated from FastAPI schema | One source of truth for types |
| Package mgmt | uv (Python), pnpm (JS) | |

## Data & analytics layer (Python)

Powers the Status Window analytics, System Reports and adaptive quests. Details: [../architecture/analytics.md](../architecture/analytics.md).

| Library | Use |
| --- | --- |
| **pandas** | Load XP/goal ledgers into DataFrames: rolling averages, streaks, weekly/monthly rollups, per-stat growth |
| **NumPy** | XP curve math, vectorised level/rank projections, Fatigue score |
| **Plotly** | Build figures server-side (`fig.to_json()`), render client-side with plotly.js using a custom System dark template |
| **SciPy** | Trend fits (linear/exponential), correlation significance (e.g. sleep vs completion) |
| **scikit-learn** | Phase 2+: predict Dungeon Break risk / likely-failed days from history |
| **statsmodels** | Optional: seasonality (weekday patterns) in completion |

## Other backend libraries

| Library | Use |
| --- | --- |
| **APScheduler** | Scheduled jobs: Gate opening, Emergency Quest drops, weekly System Report, push reminders |
| **pywebpush** | Web push notifications ("[Daily Quest has arrived.]") |
| **Pillow** | Shareable Status Window / Rank-up cards as PNG |
| **Jinja2** | HTML weekly System Report (email or in-app) |
| **argon2-cffi** | Password hashing |
| **structlog** | Structured logs |
| **Hypothesis** | Property tests for XP/level/rank math (e.g. level never decreases below Monarch) |
| **factory-boy + Faker** | Seed 90 days of fake history for UI + analytics dev |
| **ruff + mypy** | Lint, format, type-check |
| **Anthropic SDK** | Phase 3: AI System voice — generates Emergency Quests, Gate themes, weekly review |

## Other frontend libraries

| Library | Use |
| --- | --- |
| **plotly.js** (`react-plotly.js`, partial `plotly.js-basic-dist-min` bundle) | Render backend Plotly figures. Lazy-load on Stats page only — full bundle is ~3 MB |
| **tsParticles** | Mana particle / fog background |
| **Howler.js** | System chime, level-up, ARISE sound effects (muted by default) |
| **Font Awesome** (`@fortawesome/react-fontawesome`, free-solid) | Icons |
| **Zustand** | Small client state (notice queue for System windows, sound toggle) |
| **date-fns-tz** | Display countdowns in user tz |
| **Vitest + Playwright** | Unit + end-to-end tests (incl. mobile viewport) |

## Why React and not Python-only

The UI is the product here: typed-in System messages, glowing windows, count-ups, level-up sequences, smooth responsive layouts. Python-only options exist but fight that:

| Option | Verdict |
| --- | --- |
| Django/FastAPI + Jinja + HTMX + Alpine | Good for CRUD, but complex sequenced animations and optimistic UI get painful. Viable if you want minimal JS. |
| Reflex / NiceGUI / Streamlit | Fast prototypes, but limited control over custom design and motion. Not a fit for this look. |
| **FastAPI + React** | Python owns game logic + data; React owns experience. Recommended. |

Game rules live **only in the backend** (Python) so the client can't fake XP, and rules stay testable.

## Hosting (later)

- Personal: run locally, or one small VPS / Fly.io / Railway (API + SQLite volume), frontend on Vercel/Netlify/Cloudflare Pages.
- Public: managed Postgres (Neon/Supabase/Railway), same deploy.

## Open questions
- OK with React frontend, or prefer HTMX route to stay mostly Python?
- Repo layout: monorepo `backend/` + `frontend/` (proposed).
