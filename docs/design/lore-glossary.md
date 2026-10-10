# Lore Glossary

**Canonical vocabulary.** UI copy, docs, code names (models, endpoints, components) use these terms. No generic words like "task", "habit", "level tier", "boss fight", "achievement".

## 1. Story in brief

Gates — portals to dungeons full of magic beasts — opened across the world. Some people **Awakened** as **Hunters**, ranked **E to S** by the **Hunters Association**, organised into **Guilds**. Sung Jin-Woo, the weakest E-Rank Hunter ("the world's weakest hunter"), nearly dies in a **Double Dungeon**. The **System** chooses him as its only **Player**: he can **level up**, unlike every other Hunter whose power is fixed at Awakening. Daily Quests, Penalty Zones, Instant Dungeons and the Job Change Quest forge him into the **Shadow Monarch**, who raises fallen enemies with **"Arise"** into his **Shadow Army** and fights the other **Monarchs** to protect humanity.

**Theme fit:** start weakest, grow alone through relentless daily effort. That is the app.

## 2. Term → app mapping

### Identity

| Lore term | Meaning in series | In the app |
| --- | --- | --- |
| **Player** | The one person the System chose | The user |
| **The System** | Program that issues quests, rewards, penalties | The app's voice; all notices come from "the System" |
| **Awakening** | Moment a person gains power | Onboarding. Completing first full Daily Quest = Awakening (F → E) |
| **Hunter** | Awakened person | Player profile type; later, other users |
| **Hunter Rank** (E–S) | Power tier | Rank tier **F, E, D, C, B, A, S** (F = Unawakened, our addition) |
| **Reassessment** | Re-measuring a Hunter's rank at the Association | Rank-up event after clearing that rank's Gate (see Gates) |
| **Status Window** | Level, HP, MP, Fatigue, stats, title, job | Profile/status screen |
| **Stats** — STR, VIT, AGI, INT, PER (Sense) | Attributes | Same 5 stats, mapped in game-mechanics §3 |
| **Ability Points** | Free points to allocate on level up | Open question — allocatable points |
| **Title** | Earned epithet with effect ("Wolf Slayer") | Earned from Hidden Quests / milestones |
| **Job** / **Job Change Quest** | Class change trial (→ Necromancer) | Phase 3: one-time trial at Rank B; pick a Job (e.g. Fighter, Scholar, Assassin, Monk) giving stat XP bonus |
| **Fatigue** | Status meter; high fatigue hurts performance | Phase 2: burnout signal from overloaded days; suggests Recovery |

### Quests

| Lore term | In the app |
| --- | --- |
| **Daily Quest** ("Preparations to Become Powerful") | Recurring daily objectives. Default pack mirrors the anime: 100 push-ups, 100 sit-ups, 100 squats, 10 km run (scalable) |
| **Routine** | A named set of Goals. Each weekday has its own day type and runs up to 2 Routines (Training days need one). Awakening creates Training/Standard/Recovery Day Routines plus a "Daily Routine" (water, sleep…). Edited on the Plan page |
| **Goal** (list inside quest window) | Objective rows with `[target]` |
| **Quest Reward** | XP, Gold, Ability Points, Random Box |
| **Penalty / Penalty Zone** | Failed Daily Quest → **Penalty Quest** in the **Penalty Zone** (themed red screen, must survive/clear) |
| **Emergency Quest** | Sudden, time-limited, high reward |
| **Hidden Quest** | Secret conditions, revealed on completion → Title |
| **Job Change Quest** | See Identity |

### Gates & Dungeons

| Lore term | In the app |
| --- | --- |
| **Gate** | Weekly challenge with a rank (E–S). Enter = commit to a set of quests over its duration |
| **Dungeon** | The content inside a Gate (the week's quest set) |
| **Dungeon Boss** | Final objective of the Gate (e.g. Sunday long run). Clearing it clears the Gate |
| **Gate Rank** | Difficulty; your rank sets which Gates you can enter |
| **Dungeon Break** | Gate not cleared before it closes → monsters "escape": next week starts with a debuff (lower XP mult) until a recovery quest is cleared |
| **Red Gate** | Rare, B-rank+ hard Gate. Once entered, no leaving: can't abandon, no Recovery days, big reward |
| **Instant Dungeon** + **Instant Dungeon Key** | Key (crystal) randomly drops on Daily Quest clear → private dungeon of 2–3 Extra Goals + Boss → loot. Focus Dungeon variant = timed deep-work session. See drops-and-instant-dungeons.md |
| **Double Dungeon** | Hidden Gate behind a normal one; appears rarely after clearing a Gate perfectly |
| **Raid** / **Strike Team** | Phase 3: group Gate with other Hunters |
| **Clear** | Completing a Gate / Dungeon |

### Loot & economy

| Lore term | In the app |
| --- | --- |
| **Gold** | Main currency (System currency in series) → **Shop** |
| **Shop** | Spend Gold on user-defined real-life rewards + cosmetics |
| **Inventory** | Holds Keys, Random Boxes, Potions, cosmetics |
| **Random Box** | Loot drop from Gate clears / milestones |
| **Mana Crystal** | Common loot from Gates; converts to Gold |
| **Essence Stone** | Rare loot from Bosses; used for rank-up / crafting cosmetics |
| **Potion / Status Recovery** | Recovery (rest) day token. Using one = "Full Recovery" |

### Shadow Army (phase 2 signature feature)

| Lore term | In the app |
| --- | --- |
| **Shadow Extraction — "ARISE"** | Once an objective is mastered (e.g. 66-day streak), the Player can extract it as a **Shadow** |
| **Shadow Soldier** | A mastered habit. Gives small passive buff (e.g. +5% stat XP for its stat) and keeps running at reduced tracking |
| **Shadow grades** — Normal → Elite → Knight → Elite Knight → Commander → Marshal → Grand Marshal | Shadow levels up the longer the habit holds |
| **Shadow Army** | Collection screen of all extracted shadows |
| **Monarch** | Ultimate long-term goals ("Monarch of Fitness") — epic multi-month Gates |
| **Shadow Monarch** | Endgame title |

### Social (phase 3)

| Lore term | In the app |
| --- | --- |
| **Guild** | Group of Hunters with shared Gates |
| **Hunters Association** | Global leaderboard / rank registry |
| **National Level Hunter** | Top-ranked public Hunters |

## 3. System notice templates

```
[Daily Quest: Preparations to Become Powerful has arrived.]
[WARNING: Failure to complete the Daily Quest will result in an appropriate penalty.]
[Quest Complete. Rewards: +120 XP, +60 Gold.]
[Level Up!]
[You have entered the Penalty Zone.]
[A Gate has opened. Rank: C. Time remaining: 6d 23h.]
[Dungeon Boss defeated. Gate cleared.]
[Dungeon Break.]
[Emergency Quest has arrived.]
[Hidden Quest cleared. Title acquired: Early Riser.]
[Reassessment complete. Hunter Rank: D.]
[Shadow Extraction available. ARISE.]
```

## 4. Notes
- Story summary from [Wikipedia](https://en.wikipedia.org/wiki/Solo_Leveling). Red Gate / Dungeon Break / Mana Crystal / Essence Stone details from [Sportskeeda](https://sportskeeda.com/anime/what-red-gate-solo-leveling-explained), [Beebom](https://beebom.com/red-gates-solo-leveling-explained/amp/), [GamePro](https://www.gamepro.de/artikel/solo-leveling-red-gates,3426041.html), [Solo Leveling Wiki – Mana Crystals](https://solo-leveling.fandom.com/wiki/Mana_Crystals).
- Instant Dungeon, Dungeon Key, Penalty Zone details, Shadow grades and Daily Quest name are from memory of the series — verify.
- Public release: use these generic genre terms freely, but not "Solo Leveling", character names (Sung Jin-Woo, Igris, Beru) or official art.
