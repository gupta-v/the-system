# Drops & Instant Dungeons

In the series, clearing a quest gives more than XP — the System hands out **Random Boxes**, items and **Instant Dungeon Keys** that open a private dungeon only the Player can enter. We copy that: clearing the Daily Quest sometimes drops a Key (a glowing crystal) that teleports the Player into a short **Instant Dungeon** of 2–3 extra challenges. Clear it → loot.

Lore check: Instant Dungeon Key as quest reward + Random Box are from memory of the series — verify. See [lore-glossary.md](lore-glossary.md).

## 1. Flow

```
Daily Quest cleared
   │  drop roll (§2)
   ▼
[Reward: Instant Dungeon Key (D-Rank) acquired.]      ← key goes to Inventory, crystal animation
   │  Player taps "Use Key" (any time before key expires)
   ▼
[You have entered the Instant Dungeon: Cursed Forest.]  ← teleport animation, screen tint
   │  2–3 Extra Goals + timer
   ▼
Clear all  → [Dungeon cleared.] → loot roll (§5)
Time out   → [The dungeon has collapsed.] → key lost, no penalty
```

- Optional. Never penalised beyond losing the key.
- Max **1 Instant Dungeon per day** (a 2nd key waits in Inventory).
- Extra Goals do **not** count toward Daily Quest completion; they're pure bonus.

## 2. Drop rules

Drops only roll when the Daily Quest is **fully cleared** — the reward is for finishing.

| Factor | Effect |
| --- | --- |
| Base drop chance | 30% per cleared day |
| Streak | +2% per streak day, max +20% |
| Difficulty | Elite +2.5%, National +5%, Reawakened +7.5%, Monarch +10% |
| Pity timer | Guaranteed drop after 4 cleared days without one |
| Recovery Day | No key drops (rest is rest); small chance of a Potion |

Expected: ~2 keys/week for a consistent Player. Rare, not routine.

**Key rank** = usually Player's rank; 10% chance one rank higher (harder, better loot). Key colour = rank colour (ui-style-guide RankBadge).

**Key expiry:** 48h. `[The key will crumble in 6h.]` — urgency without punishment.

## 3. Instant Dungeon content

### Generation
System picks 2–3 Extra Goals from a pool, filtered and weighted by:
1. **Today's day type** — Recovery Day → only light/mind Goals; Training Day → physical OK.
2. **Rank scaling** — `+10 push-ups` at E, `+25` at B.
3. **Weakest stat** — favour the stat lagging most (balances the Player).
4. **Time left before reset** — no "2 hours no phone before sleep" if it's already 23:30.
5. **No repeats** of yesterday's dungeon Goals.

Last Goal = **Dungeon Boss** (slightly harder, marked with a skull/crest).

### Extra Goal pool (starter)

| Stat | Examples |
| --- | --- |
| STR | +10 push-ups · +20 squats · 1 min plank · 10 burpees |
| AGI | +1 km run · 10 min jump rope · 2,000 extra steps · 10 min stretching |
| VIT | +500 ml water · in bed by 23:00 · no junk food rest of day · 1 fruit/veg serving |
| INT | +10 pages reading · 25 min focused study · learn 10 new words · write 1 journal page |
| PER | No phone 2h before sleep · 10 min meditation · cold shower · no social media for 3h |

Player can add own Goals to the pool and ban ones they never want.

### Time limit
- Physical Goals: 2h from entering.
- Behaviour Goals ("no phone 2h before sleep", "in bed by 23:00"): run until next reset; confirmed at evening check-in / next morning (`[Did you keep the seal? Yes / No]`).

### Dungeon variants

| Variant | Trigger | Content | Loot |
| --- | --- | --- | --- |
| Instant Dungeon | Normal key | 2 Goals + Boss | Standard |
| Focus Dungeon | Key variant (INT/PER) | One timed deep-work / no-phone session (timer in app) | Standard + INT/PER stat XP |
| Double Dungeon | 5% chance on entering: `[Warning: this is a Double Dungeon.]` | 3 Goals + harder Boss | 2× loot, rare item chance |
| Red Key | Rare drop, B-rank+ | Red Gate rules: can't quit once entered | Essence Stones, rare items |

## 4. Rewards per clear

- **XP:** +10 per Goal, +20 Boss (rank-scaled), outside the daily 100 budget. Capped at +50% of a day's XP so dungeons speed progress but can't replace Daily Quests.
- **Stat XP** for each Goal's stat.
- **Gold + Mana Crystals.**
- **Loot roll** (§5).

## 5. Goodies (loot) — draft, to refine

Principle: **goodies make the grind smoother or more fun, never let you skip the work.** No item clears a whole Daily Quest.

| Item | Rarity | Effect | Why it helps |
| --- | --- | --- | --- |
| Mana Crystal | Common | Converts to Gold | Feeds Shop (real-life rewards) |
| XP Elixir | Uncommon | +25% XP tomorrow | Motivates showing up next day |
| Recovery Potion | Uncommon | One unplanned rest day without penalty | Sick days / emergencies |
| Reroll Scroll | Uncommon | Swap one Goal today for an equal-difficulty alternative | Flexibility without lowering bar |
| Streak Shield ("Stealth") | Rare | Protects streak once on a failed day (penalty still applies) | Softens a single bad day |
| Ability Point | Rare | +1 allocatable stat point | Series-faithful |
| Essence Stone | Rare | Needed (with Gate clear) for Reassessment at B+ | Gives keys real purpose late-game |
| Rune Stone | Epic | Unlocks a Skill (phase 2: e.g. "Sprint" +10% AGI XP for a week) | Long-term build choices |
| Cosmetics | Varies | System window skins, glow colours, titles, profile frames | Pure flex |
| Random Box | — | Opens into any of the above | Surprise |

Open: which goodies are real utilities vs cosmetics; balance numbers; should some be tradeable in Guilds later.

## 6. Data model additions

```
items               id, code, name, rarity, kind (key|consumable|material|cosmetic|box), effect (json)
inventory_items     id, user_id, item_id, qty, acquired_at, expires_at, source_ref
drop_events         id, user_id, daily_quest_id, roll, result_item_id, pity_counter
extra_goal_pool     id, user_id (null = system), stat, text, min_rank, kind (physical|behaviour|focus),
                    target_by_rank (json), allowed_day_kinds, banned (bool)
dungeon_runs        id, user_id, key_item_id, variant, rank, goals (json), boss_index,
                    entered_at, expires_at, status (active|cleared|collapsed), loot (json)
```

Drop/loot rolls live in the engine with a seeded RNG per (user, date) — reproducible, testable, no re-roll by refreshing.

## 7. Phase

**Decided: whole feature ships in Phase 2.** MVP has no drops, keys or Inventory.

| Phase 2a | Phase 2b | Phase 3 |
| --- | --- | --- |
| Key drops, Instant Dungeon (2 Goals + Boss), XP/Gold/Mana Crystal rewards, Inventory list | Full loot table, Focus/Double Dungeons, Red Keys, Skills, cosmetics | AI-generated themed dungeons and Goals, Guild trading |

## Open questions
- 30% base drop rate — too generous / too rare?
- Should behaviour Goals (no phone) be honour-system only, or later verified (screen-time integrations)?
