# Rules

The System's rules as they work **today**, in one place. Update this file whenever a rule changes,
and add a line to the changelog at the bottom.

- Numbers live in `backend/app/config/` (`game.py`, `titles.py`, `presets.py`). If this file and the
  config disagree, the config wins — fix this file.
- The in-app **Rules** scroll reads the same numbers from `GET /rules`.
- Design intent and rationale: [game-mechanics.md](game-mechanics.md). Vocabulary: [lore-glossary.md](lore-glossary.md).

## 1. Daily Quest

1. A new Daily Quest is issued every game day. The game day starts at your **reset hour** in your
   timezone (default 04:00), so late nights count for the previous day.
2. Its Goals come from your **weekly plan** (Regimen). Each weekday has a **day type** (Training,
   Standard or Recovery) and **up to 2 Routines** (named sets of Goals); their Goals are merged and the
   first Routine names the quest. **Training days need at least one Routine.** A day with nothing
   picked is a **Standard day** and runs the **Default Routine** (starts as Sleep + Water; editable,
   can't be renamed or deleted). A Recovery day with no Routines is a **Rest Day**.
   - **Standard days** are maintenance: they can't fail, the streak is kept (not raised), no XP;
     clearing every Goal pays a flat **5 Gold** at any difficulty and rank.
   - A day with no Goals at all is neutral the same way, with no Gold.
3. Goals marked "scales with rank" are scaled by Hunter Rank (§6).
4. Goal targets are snapshotted when the quest is issued; editing a Goal later doesn't change past days.
   **Sets** (optional, 2–20) split a Goal into taps: each tap = target ÷ sets, hold the box to clear.
   Sets done count toward completion, so XP, the fail threshold and penalties follow them (2 of 4 sets = 50%).
5. **Sleep** counts the night *before* the game day: checking it on the 23rd means you slept on the
   night of the 22nd (bed by 23:59) and woke on the 23rd. Log it in the morning.
5. Only today's quest can be logged. Past days are read-only (History).
6. A day is closed at the reset. Days you never opened are closed with 0 progress.

## 2. XP, Gold, Stats

| Rule | Value |
|---|---|
| Fully cleared day | **100 base XP**, shared between its Goals by weight |
| Partial numeric Goal | XP in proportion to progress |
| Clear-all bonus | **+20%** when every Goal is done |
| Difficulty multiplier | see §3 |
| Gold | **0.5 Gold per XP** |
| Stats (STR, VIT, AGI, INT, PER) | start at **10**, +1 per **50** stat XP from Goals of that stat |

- More Goals don't mean more XP: the 100 is shared.
- XP is credited live as you log; lowering progress takes it back.
- Level, stats and Gold are always recomputed from the ledgers.

## 3. Difficulty

| Mode | Fails below | XP | XP lost on a failed day | Max Potions | Strikes |
|---|---|---|---|---|---|
| Awakened | 60% | 1.0× | none | 5 | — |
| Elite | 70% | 1.1× | 5% of progress inside the current level (never drops a level) | 4 | — |
| National | 80% | 1.2× | 10% of progress inside the current level (never drops a level) | 3 | — |
| Reawakened | 90% | 1.3× | 15% of progress inside the current level (never drops a level) | 2 | — |
| Monarch | 100% | 1.5× | 20% of a full level (**can drop a level**) | 1 | 3 in 30 days → Hunter Rank sealed until the Penalty Zone is cleared |

- Difficulty can be changed **once per week** (the first pick at Awakening is free).

## 4. Day results

| Result | When |
|---|---|
| **Cleared** | 100% of Goals done |
| **Passed** | at or above the fail threshold, below 100% |
| **Failed** | below the fail threshold → Penalty Zone (§5) |
| **Recovery** | a planned Recovery Day, or a day a Recovery Potion was used |
| **Open** | today, until the reset |

## 5. Penalty Zone

1. A failed day issues a **Penalty Quest**, due before the end of the **next** game day.
2. XP loss per difficulty (§3) is applied when the day closes.
3. Your streak resets.
4. A Penalty Quest left unfinished expires. If you were away so long that it would already be over,
   none is issued.

## 6. Levels and Hunter Rank

Level cost is measured in full-clear days.

| Rank | Levels | Clears per level | XP per level | Daily Quest targets |
|---|---|---|---|---|
| F | 1–4 | 1 | 100 | 20% |
| E | 5–11 | 2 | 200 | 35% |
| D | 12–19 | 3 | 300 | 50% |
| C | 20–29 | 4 | 400 | 65% |
| B | 30–44 | 6 | 600 | 80% |
| A | 45–64 | 7 | 700 | 100% (anime baseline: 100 push-ups, 100 sit-ups, 100 squats, 10 km) |
| S | 65+ | 10 | 1000 | 100% |

- Rank follows level automatically (Gates / Reassessment come in phase 2).
- About 313 perfect days on Awakened to reach S.

## 7. Recovery

### Planned Recovery Days
- Set in the weekly plan (default: Sunday). A Regimen needs at least one non-Recovery day.
- They **can't fail** and **don't break** the streak (they don't add to it either).
- Their Goals are optional and give **50% XP**.

### Recovery Potions
1. **Earned**: clear the Daily Quest of a planned Recovery Day (all its Goals) → **+1 Potion**.
   Empty Recovery Days and Potion days don't earn one.
2. **Carry limit** by difficulty: Awakened 5, Elite 4, National 3, Reawakened 2, Monarch 1. Clearing a Recovery Day at the limit earns nothing.
   **Use limit**: the same number per 14 days (any 14-day window).
3. **Use**: today only, on a **Training Day**. Not on a Recovery Day, and not once today is already cleared.
4. **Effect**: today becomes a Recovery day — it can't fail, no Penalty Quest, no XP loss, no strike;
   the streak is kept (not increased); XP for what you do is paid **in full**.
5. Lowering a cleared Recovery Day back below 100% before the reset takes its Potion back.

## 8. Streak and Titles

1. The streak counts consecutive days that didn't fail. Recovery days pause it.
2. Today counts as soon as it's fully cleared (no need to wait for the reset).
3. Milestones award a Title and Gold when the day closes:

| Streak | Title | Gold |
|---|---|---|
| 7 | Persistent | 50 |
| 21 | Unbroken | 150 |
| 66 | Iron Will | 500 |
| 100 | The Relentless | 1000 |

## 9. Planned — Relics and loot (phase 2)

Rare items from the series, earned by long-term effort, never bought. They make the grind smoother,
never skip the work. Detailed design: [drops-and-instant-dungeons.md](drops-and-instant-dungeons.md).

| Relic | Source (proposal) | Effect (proposal) |
|---|---|---|
| Holy Water of Life | 100-day streak | Restore one broken streak |
| Cup of Reincarnation | One-time, reaching Rank S | Undo one failed day (ever) |
| Instant Dungeon Key | Random drop on a cleared day | Opens an Instant Dungeon (2–3 Extra Goals + Boss) |
| Random Box | Gate clears, milestones | Random loot |
| Rune Stone | Bosses | Unlocks a Skill (e.g. +10% stat XP for a week) |
| Mana Crystal / Essence Stone | Dungeons | Gold / needed for Reassessment at B+ |
| Weapons (Knight Killer, Kasaka's Venom Fang, Baruka's Dagger, Demon King's Daggers, Kamish's Wrath) | Rank-ups and milestones | Cosmetic badges / titles |

## Open items

- Difficulty: should each level also scale Goal targets (+20% per level)? Not decided.
- Relic sources and effects above are proposals.

## Changelog

| Date | Change |
|---|---|
| 2026-10-11 | Goal **Sets**: progress counts per set (k/sets) for count and done/not-done Goals; partial sets give partial XP. |
| 2026-10-11 | Standard day = nothing picked → **Default Routine** (Sleep + Water); pays flat **5 Gold**, no XP, can't fail, streak kept. Potions: Training days only. Full clear always = 100 base XP for any Goal count (largest-remainder shares). |
| 2026-10-11 | Sleep Goal = last night's sleep (night before the game day); preset renamed "Sleep last night". |
| 2026-10-11 | **Standard days have no Routines.** Days with no Goals are neutral (like Recovery: no fail, streak kept, not raised) instead of auto-passing. |
| 2026-10-11 | Day type belongs to the **weekday**, not the Routine. Training days must have a Routine. |
| 2026-10-10 | Weekly plan uses **Routines**: up to 2 per day, first sets the day type; no Routines = Rest Day. Every-day Goals became a "Daily Routine". |
| 2026-10-10 | Potion carry limit 5/4/3/2/1 by difficulty; at most that many used in any 14 days. |
| 2026-10-10 | Added **Reawakened** between National and Monarch (90%, 1.3×, −15% of level progress, 1 Potion). |
| 2026-10-10 | Difficulty is now 4 levels: Normal → **Awakened**, new **Elite** (70%, 1.1×, −5%, 3 Potions), Hard → **National**, Hunter → **Monarch**. |
| 2026-10-10 | Recovery Potions are now **earned** by clearing Recovery Days (carry limit per difficulty), replacing the monthly allowance. Not usable on Recovery Days. |
| 2026-10-10 | A Potion never reduces XP; can't be used on an already-cleared day. |
| 2026-10-10 | Streak counts today as soon as it's fully cleared. |
| 2026-10-09 | Initial rules (MVP engine). |
