# UI Style Guide

## 1. Direction

**ref1 structure + ref2 expression.**

- From **ref1** (and ref4–8): dark theme, System windows (thin glowing border, translucent panel, blurred backdrop), bracketed counters `[50 / 100]`, `[Daily Quest: … has arrived.]` copy, list cards, bottom nav on mobile.
- From **ref2**: heavy geometric display type, oversized numbers, level badge, segmented XP bar, stat rows with icons + ▲ deltas, character/scene imagery bleeding behind content, snappy count-up motion.
- From **ref4**: desktop dashboard grid, countdown tile, strikes tile, calendar.

## 2. Color tokens

> **Current (2026-10-10): ref2 theme, dark.** Heavy grotesk (**Archivo**), orange accent (`--color-xp`), rounded `.card`s, `.chip`/`.btn` with hard 3px offset shadows that sink when pressed, angled `.level-slab`, huge count-up numbers, swipe-to-complete Goals, haptics on phones. Palette: matte black `#141414` background, beige-white text `#F3ECDD`, orange accent `#FF8A3D`, **mint** `#3EB489` (success, Recovery), **aqua** `#5FD3C8` (System voice), beige `#E8DCC4` (neutral); one colour per stat (`--color-stat-*`). Light variant = swap tokens later.
>
> **Superseded (2026-10-10): anime System look.** Icy blue/cyan glow on deep navy replaces violet; titles use **Cinzel**; panels use the `.system-frame` double border with corner brackets; Quest Info follows the series layout (`[!] QUEST INFO`, centered GOALS, `[x/y]` + green check squares, red WARNING). Live values: `frontend/src/index.css`. The table below is the original violet draft, kept for history.

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#0B0A14` | Page background |
| `--bg-elev` | `#15122A` | Cards |
| `--panel` | `rgba(30, 22, 60, 0.55)` | System window fill (with backdrop blur) |
| `--border` | `#3B2F6B` | Default card border |
| `--accent` | `#A78BFA` | Primary violet (buttons, active nav) |
| `--glow` | `#7C3AED` | Glow / box-shadow |
| `--system` | `#7DD3FC` | System notice highlight text (ref4–8 blue) |
| `--text` | `#ECE9F7` | Primary text |
| `--text-dim` | `#9A93B8` | Secondary text |
| `--success` | `#4ADE80` | Checks, ▲ deltas, +XP chips |
| `--danger` | `#F87171` | Warnings, penalty, strikes |
| `--xp` | `#FB923C` | Optional: ref2 orange for level badge / XP bar |

Open: keep `--xp` orange (ref2 energy, strong contrast on purple) or all-violet?

Dark-only for MVP.

## 3. Typography

| Role | Font | Notes |
| --- | --- | --- |
| Display / numbers | **Cinzel** (Google) — was Clash Display / Unbounded | Weight 600–700. Level number, XP, stats, page titles. ref2 feel. |
| Body / UI | **Satoshi** or **Inter** | 400–500 |
| Counters / System text | **JetBrains Mono** | `[50 / 100]`, timers, tabular numbers |

Scale (mobile → desktop): display 48→72, h1 28→36, h2 20→24, body 15→16, small 13.

Big numbers use `font-variant-numeric: tabular-nums` so count-ups don't jitter.

## 4. Components

- **SystemWindow** — modal/panel: 1px `--system` border, outer glow, inner gradient, title chip `[i] QUEST INFO`, corner close. Used for every System notice.
- **QuestCard** — title, subtitle ("Daily Quest" / "Personal Added"), right-aligned `[x / y]`, tap to log. States: todo, partial, done (moves to Completed, dims).
- **ObjectiveRow** — label, `[target]`, checkbox or stepper. Checkbox glows green on complete.
- **LevelBadge** — angled orange/violet badge with huge number + "LEVEL" (ref2).
- **SegmentedXPBar** — 20–30 segments, fills left→right, last segment pulses. "36 XP to Lvl 34".
- **RankBadge** — letter F–S in a hex/shield frame. Colors: F gray, E green, D blue, C cyan, B violet, A red, S gold with animated glow.
- **StatRow** — icon, name, ▲ delta, big number.
- **CountdownTile** — time to reset, segmented border that drains (ref4).
- **StrikesTile** — `0 / 3` (Monarch).
- **Chip** — streak 🔥, titles 🏆, gold ✦ (ref3 top bar).
- **Calendar heatmap** — month grid, cell intensity = completion %.
- **BottomNav** (mobile) — Quest, Inventory, Rating, History, Profile. Rules (scroll icon) and Log out sit in the header.

## 5. Motion

Library: Motion (Framer Motion). All motion off/reduced under `prefers-reduced-motion`.

| Moment | Animation |
| --- | --- |
| System window open | Horizontal line draws → panel expands vertically → border glow flickers once → text types in (~25 ms/char) |
| Quest arrived | System window auto-opens on first visit after reset |
| Objective complete | Checkbox fill + glow pulse, `+10 XP` floats up and fades |
| XP gain | Segmented bar fills segment by segment, number counts up |
| Level up | Full-screen dim, `[LEVEL UP!]` scales in with glow, level number flips old→new, stat deltas stagger in |
| Penalty | Red tint, screen shake (subtle, 150 ms), warning window |
| Page transitions | Fade + 8px slide, 200 ms |
| Background | Slow drifting particles / fog behind hero art (canvas, low cost, paused when tab hidden) |

Optional sound effects (System chime, level-up) — muted by default.

## 6. Imagery

- ref1/ref2 use character art behind content with gradient fade to background.
- **Must use original or licensed art** — no official Solo Leveling art if ever public. Options: commissioned art, own AI-generated art (check license), abstract shadow/silhouette + particles.
- Hero image on onboarding and status page; subtle silhouette on level-up screen.

## 7. Responsive layout

| Breakpoint | Layout |
| --- | --- |
| < 640px (mobile) | Single column, bottom nav, System windows full-width sheets |
| 640–1024px (tablet) | Two-column cards, bottom nav or rail |
| ≥ 1024px (desktop) | Top bar + 3-column dashboard grid (ref4): Welcome / Level / Countdown, then Daily Quest + Strikes, then calendar. Max width 1200px, centered |

Touch targets ≥ 44px. Safe-area insets for PWA on iOS.

## 8. Copy voice

System speaks in brackets, terse, slightly ominous:

- `[Daily Quest: Strength Training has arrived.]`
- `[WARNING: Failure to complete the daily quest will result in an appropriate penalty.]`
- `[You have leveled up!]`
- `[Title acquired: Early Riser]`
- `[Penalty Quest: Survive.]`
