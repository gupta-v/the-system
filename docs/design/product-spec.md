# Product Spec

## 1. Vision

You are the Player. The System assigns quests from your real goals, tracks you without mercy, and rewards growth with levels, stats, ranks and titles. Make discipline feel like grinding a game you actually want to win.

## 2. Users

- **Now:** single user (owner). Daily driver on phone + desktop.
- **Later:** public sign-up. Possible social layer (guilds/parties, leaderboards).

## 3. Core loop

```
Daily reset → [Daily Quest has arrived] → log objectives → XP + stat gains + gold
     ↑                                                        ↓
 penalty / streak ← missed?           level up → rank trial → new rank / title
```

## 4. Features

### MVP
- **Onboarding / Awakening** — intro screen ("Your awakening begins now"), pick name, timezone, reset hour, difficulty, starter quest pack.
- **Status window** — level, XP bar, rank, title, 5 stats, streak, gold.
- **Daily Quest** — set of objectives with targets (`[50/100]`, `[3L]`, `[7hrs]`) and checkbox or numeric progress. Countdown to reset.
- **Regimen** — weekly plan set up via a short System interview (~7 taps): Training / Standard / Recovery days, Goals per day type, auto-repeats weekly, edit "this week" or "from now on". Quick-log ≤ 3 taps/day. See [regimen.md](regimen.md).
- **Quest management** — create/edit/archive Goals; target, unit, stat tag, XP weight, rank scaling.
- **Bonus objectives** — "Complete all" bonus, multipliers (ref7).
- **Penalties** — per difficulty mode (see game-mechanics.md §6). Strikes counter.
- **System notifications** — in-app animated System windows: quest arrived, quest complete, level up, penalty, title earned.
- **History** — calendar heatmap of completion (ref5), per-day detail.
- **Responsive** — mobile bottom nav, desktop dashboard grid. Installable PWA.

### Phase 2
- Emergency Quests (sudden, time-limited, bonus reward).
- Hidden Quests → Titles.
- Gates & Dungeons: weekly ranked Gate, Dungeon Boss, Dungeon Break, Red Gates, Double Dungeons.
- Reassessment (rank-up via clearing that rank's Gate).
- Instant Dungeons: Dungeon Key → timed focus session.
- Shadow Army: ARISE mastered Goals into Shadow Soldiers.
- Shop + Inventory: Gold, Random Boxes, Mana Crystals, Essence Stones, Recovery Potions.
- Workout plans (ref6: day N, exercises, sets/reps/tempo, locked progression).
- Web push notifications (reset reminder, quest arrived).
- Stats/analytics page (stat growth over time, ref2 "Day 1 vs Day 66").

### Phase 3 (public)
- Multi-user auth, onboarding polish, data export.
- Parties/guilds, leaderboards, shared gates.
- AI "System" voice: generates quests, weekly review.

## 5. Non-goals (for now)
- Native mobile apps (PWA covers it).
- Integrations with fitness trackers (maybe later: steps, sleep).
- Social feed.

## 6. Success criteria (personal phase)
- Owner uses it daily for 66 days.
- Logging a full day takes < 60 seconds.
- Works offline-tolerant on phone (log now, sync later — nice-to-have).

## Open questions
- Starter quest pack content — fitness-only like the anime, or balanced (body/mind/discipline)?
- Do we need free-text journal per day?
