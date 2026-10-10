# Docs Index

Self-improvement web app inspired by the System from *Solo Leveling*. Real-life habits become quests; completing them levels you up.

| Folder | Contents |
| --- | --- |
| [implementation/plan.md](implementation/plan.md) | **Build status**: phases, todo, open items, updates log |
| [implementation/fixes.md](implementation/fixes.md) | Bugs found and how they were fixed |
| [design/product-spec.md](design/product-spec.md) | Vision, users, features, MVP scope |
| [design/rules.md](design/rules.md) | **Current rules** (as implemented) + changelog. Keep in sync with `backend/app/config/` |
| [design/game-mechanics.md](design/game-mechanics.md) | XP, levels, stats, ranks, quests, penalties, rewards (design intent) |
| [design/regimen.md](design/regimen.md) | Custom weekly plans, rest days, prompts, ≤ 3-tap logging, repeat/edit |
| [design/drops-and-instant-dungeons.md](design/drops-and-instant-dungeons.md) | Random Key drops, Instant Dungeons (2–3 Extra Goals), loot/goodies |
| [design/lore-glossary.md](design/lore-glossary.md) | **Canonical vocabulary** — lore terms → app features. Use in all copy and code |
| [design/ui-style-guide.md](design/ui-style-guide.md) | Visual direction, colors, type, motion, responsive layout |
| [stack/tech-stack.md](stack/tech-stack.md) | Proposed stack and alternatives |
| [architecture/overview.md](architecture/overview.md) | System design, data model, API surface |
| [architecture/analytics.md](architecture/analytics.md) | pandas/NumPy/Plotly analytics, Fatigue, adaptive quests, System Report |
| [implementation/roadmap.md](implementation/roadmap.md) | Phased build plan |

## Decisions log

| # | Decision | Status |
| --- | --- | --- |
| D1 | Audience: personal use first, data model ready for multi-user/public later | Decided |
| D2 | Visual: ref1 layout/colors/System windows + ref2 typography, stat presentation, imagery and motion | Decided |
| D3 | Failure harshness: configurable difficulty (Awakened / Elite / National / Reawakened / Monarch) | Decided |
| D3b | Rank tiers: F, E, D, C, B, A, S (F = unawakened start) | Decided |
| D3d | Progression: 1 clear = 1 level at F, a week per level at A, 10 days at S; Daily Quest targets scale by rank (F 20% → A 100%). S ≈ 313 perfect days | Decided |
| D3e | Drops, Instant Dungeons, loot/Inventory → Phase 2 (not MVP) | Decided |
| D3c | Lore-accurate vocabulary everywhere (Player, Gates, Dungeons, Hunter Rank, Penalty Zone, ARISE…) — see lore-glossary.md | Decided |
| D3f | Backend layout: `api/` → `core/` (use-case flows) → `services/` (per-domain, modular monolith) → `repositories/` (all DB code, DB tables in `repositories/db_schema.py`) + `utils/` + `models/` (Pydantic); no `schemas/` folder | Decided |
| D4 | Backend in Python (FastAPI); React frontend for animation-heavy UI | Proposed — confirm |
| D5 | App name: **The System**. Branding for public release still avoids "Solo Leveling" trademark + official art | Decided (name) |
| D6 | Hosting: backend on Render (SQLite on a persistent disk), frontend on Vercel with an `/api` rewrite. DB choice for public launch still open | Decided |

## Open questions

See bottom of each doc. Master list:

1. ~~App name?~~ → **The System** (D5)
2. Stats: earned only from tagged quests, or also free allocatable points on level-up? (game-mechanics.md §3)
3. Accent color: pure violet, or violet + orange XP accent from ref2? (ui-style-guide.md §2)
4. Workout tracker (ref6-style sets/reps/tempo) in MVP or phase 2?
5. ~~Hosting target?~~ → Render + Vercel (D6). Still open: DB for public launch (Postgres/Neon?)

## References

`/references/ref1.png` – `ref8.png`. Summary:

- **ref1** — "Awaken" mobile app. Dark purple, glowing System panels, Daily Quests / Plan / Completed lists, `[50/100]` counters, Quest Info modal with penalty warning, bottom nav.
- **ref2** — "Your Rating". Heavy geometric display font, huge numbers, level badge, segmented XP bar, stat rows with ▲ deltas, character art bleeding behind content.
- **ref3** — 66-day habit game. Streak/trophy/currency chips, "Next Monster" countdown, day X/66, task completion buffs a character for a fight.
- **ref4–ref8** — "Badhunter" desktop web. Blue glow System theme, dashboard cards (Level, Countdown, Daily Quest 6/12, Strikes 0/3), training plan with locked days, calendar, workout table (sets/reps/tempo), Quest Info modal with bonus objectives (+XP / +30% XP).
