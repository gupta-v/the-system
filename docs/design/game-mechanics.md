# Game Mechanics

All numbers are starting values — tune after a few weeks of real use. Keep them in one config module, never hardcoded in UI.

## 0. Source: how the System works in Solo Leveling

From the series (from memory — web wiki was not reachable; verify details if accuracy matters):

- **The Player** — Jin-Woo is the only one with a System. It speaks in bracketed notices: `[Daily Quest has arrived.]`, `[You have leveled up!]`.
- **Status window** — Name, Level, Job, Title, HP, MP, Fatigue; stats **STR, VIT, AGI, INT, PER (Sense)**; available ability points.
- **Daily Quest: "Preparation to become strong"** — 100 push-ups, 100 sit-ups, 100 squats, 10 km run. Every day.
- **Penalty Zone** — failing the daily sends him to a survival dungeon for hours. Warning shown on the quest: *"Failure to complete the daily quest will result in an appropriate penalty."*
- **Rewards** — full status recovery, ability points, random boxes, gold, items.
- **Quest types** — Daily, Emergency (sudden, must do now), Hidden (secret conditions), Job Change (class-advancement trial dungeon).
- **Other** — Inventory, Shop, Skills (active/passive), Titles with effects (e.g. "Wolf Slayer"), Instant Dungeons (keys), Hunter ranks E→S (we extend to F→S, see §4).

We map each to a real-life equivalent below.

## 1. XP and levels

**Principle: early levels come in a day, late levels take a week+. Quests get harder as rank rises. S-Rank is earned over a year.**

- **Fixed daily XP budget:** a fully cleared Daily Quest = **100 base XP**, whatever the number of Goals. Each Goal's XP = its weight share of 100. Adding more trivial Goals can't farm XP.
  - Partial numeric progress: `floor(goal_xp * progress/target)`.
  - Multipliers on top: difficulty (§6), Bonus Goals, Gates, Shadows.
- **Level cost is measured in full-clear days:** `xp_to_next(L) = 100 * days_per_level(rank_of(L))` (table in §4).
  - F: 1 clear = 1 level. A: 7 clears (one full week) = 1 level. S: 10 clears per level.
  - A missed or partial day stretches it further.
- **XP ledger is source of truth.** Every gain/loss is an event row; level is derived. Makes recalcs and undo safe.
- No level-down on Awakened. See §6 for the other levels.

## 2. Gold

- Earned alongside XP (`gold = xp / 2`) plus bonuses.
- Spent in Shop on user-defined rewards (phase 2): "1 hr gaming = 150g", "cheat meal = 400g".

## 3. Stats (STR / VIT / AGI / INT / PER)

| Stat | Real-life meaning | Example quests |
| --- | --- | --- |
| STR | Strength | Push-ups, gym, strength workout |
| VIT | Health / recovery | Sleep 7h, water 3L, protein, no junk |
| AGI | Cardio / mobility | Run, walk 6k steps, stretching |
| INT | Learning / mind | Read 20 pages, study, deep work 2h |
| PER | Focus / discipline | Meditation, no phone first hour, no sugar |

- Each objective tagged with one stat. Completing it adds stat XP; every 50 stat XP = +1 stat. Stats show ▲ deltas vs yesterday / day 1 (ref2).
- **Open:** also grant 3 free ability points per level for player to allocate (anime-faithful, but disconnected from real effort)? Proposal: yes, but cap allocated points to ≤ 20% of a stat's total so real activity dominates.

## 4. Ranks

Seven tiers: **F → E → D → C → B → A → S**. (The series uses E→S; F is our addition — the "unawakened" starting tier.)

| Rank | Levels | Clears per level | XP per level | Days in rank | Reached on day* | Daily Quest intensity | Flavor |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F | 1–4 | 1 | 100 | 4 | 1 | 20% | Unawakened |
| E | 5–11 | 2 | 200 | 14 | 5 | 35% | Awakened. Habit forming |
| D | 12–19 | 3 | 300 | 24 | 19 | 50% | Consistent |
| C | 20–29 | 4 | 400 | 40 | 43 | 65% | Disciplined |
| B | 30–44 | 6 | 600 | 90 | 83 | 80% | Elite |
| A | 45–64 | 7 (a week) | 700 | 140 | 173 | 100% (anime baseline) | Top tier |
| S | 65+ | 10 | 1000 | — | **313** | 100% + S-rank challenges | Monarch-level |

\*Perfect run on Awakened (1.0×), no Gate delays. Realistic (~80% clear rate, Gates): **S-Rank ≈ 13–15 months.** Monarch (1.5×) shortens it but punishes misses.

Cumulative XP to S ≈ 31,200.

**Quests get harder with rank ("Daily Quest intensity").** The System's default Daily Quest — *Preparations to Become Powerful* (100 push-ups, 100 sit-ups, 100 squats, 10 km run at 100%) — scales its targets by rank:

| Rank | Push-ups / sit-ups / squats | Run |
| --- | --- | --- |
| F | 20 | 2 km |
| E | 35 | 3.5 km |
| D | 50 | 5 km |
| C | 65 | 6.5 km |
| B | 80 | 8 km |
| A | 100 | 10 km |
| S | 100 + rotating S-rank challenges (e.g. weighted, timed, 15 km) | |

- Custom Goals can opt in to rank scaling (`scales_with_rank: true`) with their own F and A targets; the System interpolates between.
- On Reassessment the System announces new targets: `[Hunter Rank: D. The Daily Quest has been adjusted.]`
- Adaptive targets (analytics.md) fine-tune within a rank; rank scaling sets the floor.

Each rank gets its own badge color/glow in UI (F gray → S gold/violet).

**Awakening (F):** first fully cleared Daily Quest = Level 1 → 2 with the Awakening sequence (`[You have been chosen as a Player.]`). F → E happens automatically at Level 5 (F has no Gate).

Phase 2: reaching a rank's level cap unlocks that rank's **Gate**. Clearing it triggers **Reassessment** → next Hunter Rank. XP keeps accumulating but rank stays until the Gate is cleared.

Terminology for everything below: [lore-glossary.md](lore-glossary.md).

## 5. Quests

| Type | Behavior | Phase |
| --- | --- | --- |
| Daily Quest | Recurring Goals, reset at user's reset hour | MVP |
| Bonus Goals | "Complete all Goals" (+20% day XP), "Complete strength workout" (+30%) | MVP |
| Penalty Quest | Failed Daily Quest → Penalty Zone; must clear before next day ends | MVP |
| Emergency Quest | Sudden, e.g. "Cold shower in the next 2 hours", 2× XP, optional | 2 |
| Hidden Quest | Secret conditions (7-day streak, 100 push-up days…) → Title | 2 |
| Job Change Quest | One-time trial at Rank B → choose a Job | 3 |

## 5b. Gates & Dungeons (phase 2)

| Element | Rule |
| --- | --- |
| Gate | Opens weekly, has a Gate Rank. Inside = Dungeon (set of quests for the week) |
| Dungeon Boss | Final objective; defeat + ≥ 80% Dungeon completion = Gate cleared → Random Box, Mana Crystals |
| Dungeon Break | Gate not cleared by close → next week −20% XP until recovery quest cleared |
| Red Gate | Rare (B+). Can't abandon, Recovery disabled, 2× loot + Essence Stones |
| Double Dungeon | Rare hidden Gate after a perfect clear |
| Instant Dungeon | Random Key drop on Daily Quest clear → 2–3 Extra Goals + Boss → loot. See [drops-and-instant-dungeons.md](drops-and-instant-dungeons.md) |

## 5c. Shadow Army (phase 2)

Goal held 66 days → **Shadow Extraction ("ARISE")** → becomes a Shadow Soldier: +5% XP for its stat, tracked lightly. Grades rise with time held (Normal → Elite → Knight → … → Grand Marshal).

## 6. Penalties and difficulty

A day **fails** when completion < threshold at reset. Rest days (pre-planned, limited) don't count.

| | Awakened | Elite | National | Reawakened | Monarch |
| --- | --- | --- | --- | --- | --- |
| Fail threshold | < 60% | < 70% | < 80% | < 90% | < 100% |
| Streak | Resets | Resets | Resets | Resets | Resets |
| Penalty Quest | Yes (easy) | Yes (light) | Yes (medium) | Yes (heavy) | Yes (hard) |
| XP loss | None | −5% of current level progress | −10% of current level progress | −15% of current level progress | −20%, can drop a level |
| Strikes | — | — | — | — | 3 strikes in 30 days → Hunter Rank sealed until Penalty Zone cleared |
| Recovery Potions (max held = max used per 14 days) | 5 | 4 | 3 | 2 | 1 |
| XP multiplier | 1.0× | 1.1× | 1.2× | 1.3× | 1.5× |

Higher difficulty = higher reward, so choosing it feels worth it. Difficulty change allowed once per week.

## 7. Streaks

- Streak = consecutive non-failed days. Rest days don't break it.
- Milestones: 7, 21, 66, 100 → titles + gold.

## 8. Titles

Earned from hidden quests/milestones. Show one equipped title in status window. Cosmetic in MVP; phase 2 may give small effects (e.g. "Early Riser": +5% INT XP before 9am).

## 9. Day boundary

- Reset at user-chosen hour in user's timezone (default 04:00, so late nights count for previous day).
- Evaluation is **lazy**: when the app is opened (or a request hits the API), any un-evaluated past days are closed out and penalties applied. No cron needed for single user.

## Open questions
- Free ability points on level up? (§3)
- Should partial numeric progress give partial XP or all-or-nothing?
- Fail threshold numbers.
