# Analytics Architecture

The System observes everything. This module turns the XP / Goal ledgers into insight, reports and adaptive difficulty.

## 1. Flow

```
DB ledgers (xp_events, goal_logs, daily_quests)
   │  SQLAlchemy → pandas.read_sql
   ▼
analytics/ (pure functions: DataFrame in → DataFrame / numbers out)
   │
   ├─▶ figures/   Plotly figure builders → fig.to_json()  → GET /analytics/... → react-plotly.js
   ├─▶ reports/   weekly System Report (Jinja2)            → in-app / email
   └─▶ engine/    adaptive targets, Fatigue, Gate scaling  → used by quest generation
```

Rules: analytics never writes game outcomes directly — it only feeds the engine, which stays the single authority.

## 2. Features

### Status Window analytics (ref2 "Your Rating")
| View | Computation | Chart |
| --- | --- | --- |
| Stat radar | Current STR/VIT/AGI/INT/PER vs Day 1 | Plotly `Scatterpolar`, two traces |
| Stat growth | Cumulative stat XP per day | Line, one per stat |
| XP per day | Daily XP + 7-day rolling mean (pandas `.rolling(7)`) | Bars + line |
| Clear-rate heatmap | Daily completion % by date | Calendar heatmap (GitHub-style) |
| Weekday pattern | Mean completion by weekday | Bar — "Your weakest day: Sunday" |
| Goal leaderboard | Per-Goal completion rate, streaks | Horizontal bar |

### Projections
- **Next level / rank ETA:** fit recent XP rate (NumPy / SciPy linear fit on last 14 days) → `[At current pace: Rank C in 9 days.]`
- **Shadow Extraction ETA:** days left to 66-day hold per Goal.

### Fatigue (lore: Status Window Fatigue meter)
- Score 0–100 from: load vs 28-day baseline (acute:chronic ratio), consecutive high-load days, sleep Goal misses.
- High Fatigue → System suggests a Recovery Potion; on Monarch protects against unfair Strikes ("unless overtrained", ref4).

### Adaptive quests (progressive overload)
- If a numeric Goal is cleared ≥ 90% over 14 days → propose raising target (e.g. push-ups 50 → 60).
- If < 50% → propose lowering. Player accepts/declines via System window.
- Gate difficulty scales from the Player's rolling capacity, so Gates stay challenging.

### Insights
- Correlations between Goals (e.g. sleep ≥ 7h → +18% next-day clear rate). SciPy `pearsonr`/`spearmanr`, only shown when p < 0.05 and ≥ 30 days of data.
- Phase 2+: scikit-learn classifier for "high risk of failing today" → morning Emergency nudge.

### Weekly System Report
Sunday after reset: XP gained, levels, clear rate, best/worst Goals, Fatigue trend, Gate result, one insight. Rendered in a System window; optional email.

## 3. Plotly theming

One shared template (`system_dark`) matching ui-style-guide tokens: transparent background, `--text-dim` axes, thin `--border` gridlines, stat colors fixed per stat across all charts, mono font for numbers, no Plotly logo/modebar. Responsive: `autosize`, `config={responsive: true}`.

Small inline visuals (XP bar, stat deltas, sparklines) stay as React components — Plotly only for the Stats/analytics page.

## 4. Performance

- Personal scale = few thousand rows → compute on request, cache per user per game-day (in-memory / `functools.lru_cache` keyed by last event id).
- Public scale: precompute daily rollups table via APScheduler job.

## Open questions
- Email delivery for weekly report, or in-app only?
- Do we want manual data entry for body metrics (weight, steps, sleep hours) to enrich analytics?
