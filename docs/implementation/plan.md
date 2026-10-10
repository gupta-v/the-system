# Plan

Living status of the build. Long-form phase specs live in [implementation/roadmap.md](roadmap.md);
game-rule changes are logged in [design/rules.md](../design/rules.md); bugs in [fixes.md](fixes.md).

Legend: ✅ done · 🟡 partial · ⬜ not started

## Phases

### Phase 1 — MVP (personal)

| # | Step | Status | Notes |
|---|---|---|---|
| 1 | Scaffold | ✅ | FastAPI + SQLite + Alembic, Vite React TS + Tailwind + Motion, `scripts/run-app.py` |
| 2 | Engine | ✅ | XP, levels, ranks, stats, `evaluate_day`, penalties, potions, streak |
| 3 | Data + API | ✅ | UUID v4, async SQLAlchemy, ledger XP, lazy day close, cookie auth |
| 4 | Design system | ✅ | ref2 dark theme, glass `.card`, `.chip`, `.btn`, `.level-slab`, segmented XP bar, palette (mint, aqua, beige, matte) |
| 5 | Screens | 🟡 | Done: Awakening, Quest, Inventory, Rating, History (calendar + day detail + XP Journey), Profile (+ weekly plan), Rules scroll. Plan page with Goal editor. Missing: Quest Info modal |
| 6 | Motion | ✅ | NoticeQueue (typed System text), level-up slab, count-ups, swipe-to-complete, haptics |
| 7 | Responsive + PWA | 🟡 | Responsive done. Missing: manifest, icons, install |
| 8 | Analytics v1 | 🟡 | Done: stat radar, stat sparkline, XP Journey, rank journey + level/rank ETA, clear-rate heatmap, records. Missing: XP/day chart, fake-history seed |
| 9 | Dogfood | ⬜ | Use daily for 2 weeks, then tune numbers |

### Phase 2 — Depth
Emergency/Hidden Quests, Gates & Dungeons, Reassessment, Instant Dungeons + Keys + loot, **Relics** (see rules.md §9), Shadow Army, Shop (spend Gold), workout plans, push notifications, Fatigue, adaptive targets, weekly System Report.

### Phase 3 — Public
Postgres (or Mongo), deploy, sign-up flow, original art/branding, privacy policy, export, social.

## Todo

Next first.

- [x] First git commit (09679c5)
- [x] Goal editor UI on `/plan`
- [ ] PWA: manifest, icons, install prompt
- [ ] Analytics: XP/day chart
- [ ] Leaderboards (needs multiple Players — Phase 3); meanwhile maybe "personal best weeks"
- [ ] PNG icons (192/512, apple-touch) from `public/favicon.svg` for PWA
- [ ] Quest Info modal (Goal detail: stat, XP, target scaling)
- [ ] Decide: what "difficulty +20% per level" scales (Goal targets? see Open)
- [ ] Phone access: firewall rule for :5173 (admin PowerShell)
- [ ] Dogfood 2 weeks

## Open

- Difficulty +20% per level: Goal targets (recommended), fail threshold, or XP?
- Relics: sources and effects are proposals (rules.md §9).
- Branding before going public (name decided: **The System**; still need original art/logo, no official Solo Leveling art).

## Updates

Newest first. Product-visible changes; rule changes also go in rules.md, bugs in fixes.md.

| Date | Update |
|---|---|
| 2026-10-10 | Deploy config: backend on Render (`render.yaml`, Starter + 1 GB disk for SQLite), frontend on Vercel (`frontend/vercel.json` proxies `/api` so the session cookie stays same-origin). Postgres later. |
| 2026-10-11 | Goal **Sets** (optional, Plan → Goal editor): on the quest each tap fills one set (box fills bottom-up), hold the box to clear; partial sets pay partial XP. |
| 2026-10-11 | Default Routine always first in Routines; Water + Sleep locked in it. Plan edits apply from the next quest; testing switch `SYSTEM_REISSUE_TODAY_ON_PLAN_EDIT=true` (backend/.env) also rebuilds today's open quest, keeping progress. |
| 2026-10-11 | **Default Routine** (Sleep + Water) runs on Standard days (= days with no Routine); removing a Training day's last Routine makes it Standard. Standard day: 5 Gold, no XP. Potion button only on Training days. |
| 2026-10-11 | Weekly plan: a day's Routines always listed in Routine order. Standard days take no Routines (switching a day to Standard clears them); empty days are neutral for the streak. |
| 2026-10-11 | Quest page: reset countdown is its own System NOTIFICATION card above the quest board: clock + 6 four-hour boxes (XP-bar style), WARNING in red in the last hour; Daily Quest board centred. |
| 2026-10-11 | `/plan` redesign: week row (tap a day → Training/Standard/Recovery, tap its Routines → pick up to 2), Goals as chips with **+ Add**, Routines as side-by-side columns; all rows scroll sideways; one sticky **Save plan** (returns to Profile). Profile shows the week read-only + **Customize your plan**. |
| 2026-10-10 | **Routines**: create Routine 1, 2, 3… (Goals + day type), pick up to 2 per weekday on `/plan`; first sets the day type. Every-day Goals migrated into a "Daily Routine". |
| 2026-10-10 | `/plan`: **Goal editor** (add, edit, archive), Goals per Day Type, "Every-day Goals" renamed **Daily Routine**. |
| 2026-10-10 | Profile weekly plan: weekday types only + **Customize your plan** → new `/plan` page. |
| 2026-10-10 | Rating: Rank journey (F→S ladder, level/rank ETA at 14-day pace), clear-rate heatmap (12 weeks, 7d/30d/all), Records. API `GET /me/insights`. |
| 2026-10-10 | App icon: original `[!]` System mark (replaces Vite logo). |
| 2026-10-10 | App name decided: **The System**. |
| 2026-10-10 | Account renamed **Profile** (`/profile`). |
| 2026-10-10 | XP Journey tags are icon-first: `+1` Potion, `−1` Potion used, Gold amount, `Level ↗`. Shows Potions earned. |
| 2026-10-10 | **Inventory** tab: Recovery Potions (use), Gold, Titles (equip). |
| 2026-10-10 | Potions: carry 5/4/3/2/1 by difficulty, same number usable per 14 days. |
| 2026-10-10 | Difficulty: 5 levels — Awakened, Elite, National, Reawakened, Monarch. Picker on one line. |
| 2026-10-10 | Quest card header and footer centred; cleared quest shows a random motivational line instead of the WARNING. |
| 2026-10-10 | Vite terminal logs every API call (method, path, status, ms). |
| 2026-10-10 | `api/player.py` split into `player.py` + `progress.py`. |
| 2026-10-10 | Palette: mint, aqua, beige, matte black. Removed flickering effects (aurora, flame, slab shine, XP pulse, card lift). |
| 2026-10-10 | Rules scroll (holographic, sideways) opened from the header. Rules doc `design/rules.md`. |
| 2026-10-10 | Recovery Potions earned on cleared Recovery Days; not usable on Recovery Days. |
| 2026-10-10 | History: calendar → day detail → XP Journey timeline. Weekly plan editable in Profile. |
| 2026-10-10 | Profile: Hunter name, sex, birth date, height, weight. Anime art backgrounds + glass cards. |
| 2026-10-09 | ref2 dark theme; Rating tabs, count-ups, tap feedback, stat detail. |
| 2026-10-09 | Frontend (Vite, React 19, Tailwind v4) and backend MVP API. |
