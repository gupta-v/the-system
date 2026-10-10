# Regimen — Custom Weekly Plans & Low-Friction Logging

The Player sets up a weekly **Regimen** once. The System turns it into Daily Quests, prompts on the right days, collects logs with minimal taps, and repeats next week unless told otherwise.

> "Regimen" is our term (not canon). Fits the training arc tone. Alternative: "Training Regimen". Add to lore-glossary when confirmed.

## 1. UX principles

1. **Setup < 2 minutes.** The System asks; the Player taps. No long forms.
2. **Log a day in ≤ 3 taps.** Prefilled with planned targets; "Done as planned" is one tap.
3. **Repeat by default.** Next week = this week unless the Player changes something.
4. **Edit in place.** Every change asks one question: *this week only* or *from now on*.
5. **Sensible defaults everywhere.** Every field has a default; nothing is required except picking days.

## 2. Setup: the System interview

Runs in onboarding (after Awakening intro) and anytime from "New Regimen". One question per System window, mostly tap answers:

| # | System asks | Answer type | Default |
| --- | --- | --- | --- |
| 1 | `[Choose your path.]` | Preset cards: Strength · Endurance · Scholar · Balanced · Custom | Balanced |
| 2 | `[Which days will you train?]` | Weekday chips | Mon Wed Fri |
| 3 | `[Which days will you recover?]` | Weekday chips (remaining days preselected as Standard) | Sun |
| 4 | `[How much time can you give each day?]` | 15 / 30 / 60 / 90+ min | 30 |
| 5 | `[When does your day begin?]` | Time picker | 07:00 |
| 6 | `[When should the System check on you?]` | Morning / Evening / Both | Both |
| 7 | `[Anything else the System must track?]` | Optional quick-add chips: Water, Sleep, Reading, Meditation, No sugar, Steps, + custom | — |

Output: a **draft week** shown as a 7-day strip. Player can accept (`[Accept Regimen]`) or tweak. Typical setup: 7 taps.

Phase 3: free-text setup — *"gym Mon/Wed/Fri, run Saturday, rest Sunday, read every night"* → parsed by the AI System into the same structure, then shown for confirmation.

## 3. Structure

```
Regimen
 ├─ Day Types (reusable templates)
 │   ├─ Training Day   → Push-ups, Squats, Strength Workout (Push/Pull/Legs rotation), Water, Sleep
 │   ├─ Standard Day   → Walk 6k steps, Read 20 pages, Water, Sleep
 │   └─ Recovery Day   → Sleep, Water, Stretch 10 min (light, optional bonus)
 ├─ Week schedule      → Mon: Training · Tue: Standard · … · Sun: Recovery
 └─ Overrides          → specific date changes (e.g. "Thu 16 Oct: Recovery — travel")
```

- Define a Day Type **once**, assign it to many days. Editing "Training Day" updates all training days.
- Goals can also live outside day types as **Every day** Goals (water, sleep).
- **Workout rotation:** Training Day can cycle a list (Push → Pull → Legs, ref4–6). The System picks next in rotation automatically; missed sessions don't skip the rotation.
- Rank scaling (game-mechanics §4) applies to Goals with `scales_with_rank`.

## 4. Recovery Days

- **Planned** Recovery Days (in the Regimen) are free: don't break streak, don't use a Recovery Potion, don't count as failure.
- They still have light optional Goals → small bonus XP.
- **Unplanned** rest (sick, travel) = use a Recovery Potion (limited per difficulty), or add a one-day override before the day starts.
- Guardrail: a Regimen needs ≥ 1 non-Recovery day per week; more than 3 Recovery days/week lowers XP multiplier (prevents gaming).

## 5. Prompts on the right days

| When | What | Example |
| --- | --- | --- |
| Day start (user time) | Quest arrival — push + in-app System window | `[Daily Quest: Training Day — Push has arrived. 5 Goals.]` |
| Goal-specific time (optional) | Reminder for a timed Goal | `[Reading: 20 pages. The night is yours.]` |
| Evening check-in | Remaining Goals, quick-log link | `[3 Goals remain. 4h 12m until reset.]` |
| Recovery Day | Soft message, no warning | `[Recovery Day. Restore your strength.]` |
| Before reset (Monarch) | Last warning | `[WARNING: 1h remaining. Penalty imminent.]` |

Delivered via Web Push (APScheduler + pywebpush). Push actions: **Done as planned** · **Log** · **Snooze 1h**. Quiet hours respected.

## 6. Logging (≤ 3 taps)

Quick-log screen = today's Goals as rows (ref1/ref8 style):

- **Check Goal:** tap checkbox.
- **Numeric Goal:** row shows planned target prefilled `[100 / 100]`. Tap = done as planned. Long-press / tap number → stepper with quick chips (−10, +10, half, custom).
- **Workout Goal:** opens session prefilled from last session (sets × reps × weight). "Same as last time" = one tap; edit only what changed (ref6 table).
- **All done:** `[Clear All]` button marks every remaining Goal done as planned → one-tap perfect day.
- **Backfill:** yesterday stays editable until the next reset (grace window); older days locked (Monarch: no backfill).

Phase 2: auto-logs from integrations (steps, sleep) where available.

## 7. Repeat, edit, continue

- **Auto-repeat:** each week clones the active Regimen. No action needed.
- **Sunday review** (inside weekly System Report):
  `[Week complete. Clear rate 86%.]` → **Continue** (repeat as is) · **Adjust** (opens week strip) · **New Regimen**.
- **Edits** always ask scope: *Just this week* / *From now on*. Stored as a new Regimen version effective from that week — history stays accurate.
- **Templates:** save a Regimen as a template ("Cut phase", "Exam month"); switch templates anytime.
- **Pause:** pause Regimen for N days (vacation) — counts as Recovery, doesn't break streak, capped by difficulty.

## 8. Data model additions

```
regimens            id, user_id, name, active, created_at
regimen_versions    id, regimen_id, effective_from_week, day_kinds (json, Mon..Sun), notes
day_types           id, regimen_version_id, name, rotation (json)   # a Routine; no day kind
day_type_goals      day_type_id, goal_id, target_override, sort
week_schedule       regimen_version_id, weekday (0–6), slot (0 = names the quest, 1), day_type_id   # day_types = Routines
day_overrides       user_id, date, day_type_id | recovery | custom_goals(json), reason
reminders           user_id, goal_id (nullable), kind (arrival|goal|checkin|final), time, enabled
regimen_templates   id, user_id, name, snapshot (json)
workout_sessions    id, goal_log_id, exercises (json: name, sets, reps, weight, tempo)
```

Quest generation for a date: `override → week_schedule[weekday] (≤ 2 Routines, slot 0 sets day kind; none = Rest Day) → merged Routine goals → apply rank scaling + adaptive targets → daily_quest`.

## 9. MVP cut

| MVP | Phase 2 | Phase 3 |
| --- | --- | --- |
| Interview setup, presets, Day Types, week schedule, Recovery Days, auto-repeat, edit scope, quick-log, Clear All, in-app prompts | Web push + actions, workout rotation + sessions, templates, pause, Sunday review flow, integrations | AI free-text setup and AI-suggested adjustments |

## Open questions
- Name: "Regimen" or something else?
- Should the Sunday review be mandatory (blocks next week until answered) or skippable (auto-continue)? Proposal: skippable.
- Backfill grace window: until next reset, or 24h?
