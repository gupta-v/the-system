# Roadmap

## Phase 0 — Docs & decisions (now)
- [x] Reference review
- [x] Draft product spec, mechanics, style guide, stack, architecture
- [ ] Resolve open questions (docs/README.md)
- [ ] Pick name + fonts + accent
- [ ] Optional: static HTML mockup of status + daily quest screens to lock the look

## Phase 1 — MVP (personal)
Live status per step: see [plan.md](plan.md).

1. ✅ **Scaffold** — monorepo, FastAPI + SQLite + Alembic, Vite React TS + Tailwind + Motion, lint/format, pytest.
2. ✅ **Engine** — XP/level/rank/stat functions + `evaluate_day`, full unit tests.
3. ✅ **Data + API** — models, migrations, auth, endpoints from architecture §5, lazy day evaluation.
4. **Design system** — tokens, fonts, SystemWindow, QuestCard, ObjectiveRow, SegmentedXPBar, LevelBadge, StatRow.
5. **Screens** — Onboarding/Awakening + Regimen interview, week strip editor, quick-log, Home (daily quest), Quest Info modal, Inventory, Rating (Status), History calendar, Profile (settings), Goal editor.
6. **Motion** — quest arrived, objective complete, XP fill, level up, penalty.
7. **Responsive + PWA** — mobile/tablet/desktop layouts, manifest, install.
8. **Analytics v1** — pandas rollups, stat radar, XP/day, clear-rate heatmap (Plotly), level/rank ETA. Seed fake history with factory-boy to build before real data exists.
9. **Dogfood** — use daily for 2 weeks, tune numbers.

## Phase 2 — Depth
Emergency Quests, Hidden Quests + Titles, Gates & Dungeons, Reassessment, Instant Dungeons + Key drops + loot/Inventory (drops-and-instant-dungeons.md), Shadow Army, Shop + Inventory, workout plans, push notifications (APScheduler + pywebpush), Fatigue, adaptive targets, weekly System Report, insights/correlations.

## Phase 3 — Public
Postgres, deploy, sign-up flow, original art/branding, privacy policy, export, social features.
