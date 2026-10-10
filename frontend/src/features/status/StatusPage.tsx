import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBrain,
  faCaretUp,
  faChevronDown,
  faDumbbell,
  faEye,
  faHeartPulse,
  faPersonRunning,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons'
import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'
import { CountUp } from '../../components/CountUp'
import { RankBadge } from '../../components/RankBadge'
import { Sparkline } from '../../components/Sparkline'
import { StatRadar } from '../../components/StatRadar'
import { XpBar } from '../../components/XpBar'
import type { Schemas } from '../../lib/api'
import { buzz } from '../../lib/haptics'
import { Insights } from './Insights'
import { useClearPenalty, useRating, useStatDetail, useStatus } from '../../lib/queries'

const STATS: { key: Schemas['Stat']; name: string; icon: IconDefinition; color: string }[] = [
  { key: 'STR', name: 'Strength', icon: faDumbbell, color: 'text-stat-str' },
  { key: 'VIT', name: 'Vitality', icon: faHeartPulse, color: 'text-stat-vit' },
  { key: 'AGI', name: 'Agility', icon: faPersonRunning, color: 'text-stat-agi' },
  { key: 'INT', name: 'Intelligence', icon: faBrain, color: 'text-stat-int' },
  { key: 'PER', name: 'Perception', icon: faEye, color: 'text-stat-per' },
]

type Tab = 'current' | 'day1' | 'week'

const iso = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

function StatDetail({ stat }: { stat: Schemas['Stat'] }) {
  const { data, error } = useStatDetail(stat)
  if (error) return <p className="py-3 font-mono text-sm text-danger">{error.message}</p>
  if (!data) return <p className="py-3 font-mono text-sm text-text-dim">[Loading…]</p>
  return (
    <div className="flex flex-col gap-3 pt-1 pb-4">
      <div>
        <p className="mb-1 text-xs text-text-dim">Stat XP · last 30 days · {data.xp} total</p>
        <Sparkline
          values={data.history.map((h) => h.xp)}
          label={`${stat} XP per day, last 30 days`}
        />
      </div>
      {data.goals.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {data.goals.map((g) => (
            <li key={g.name}>
              <div className="flex justify-between text-sm">
                <span>{g.name}</span>
                <span className="font-mono text-text-dim tabular">
                  {g.done_days}/{g.total_days} days
                </span>
              </div>
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-bg">
                <div
                  className="h-full rounded-full bg-xp"
                  style={{ width: `${(g.done_days / Math.max(1, g.total_days)) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-text-dim">No Goals feed this stat yet.</p>
      )}
    </div>
  )
}

/** "Your Rating" (ref2): tabs, LEVEL slab, XP earned, segmented bar, big stat rows. */
export function StatusPage() {
  const { data: s } = useStatus()
  const clearPenalty = useClearPenalty()
  const [tab, setTab] = useState<Tab>('current')
  const [open, setOpen] = useState<Schemas['Stat'] | null>(null)

  const day1 = s?.awakened_on ?? null
  // "Today" is the server's game day (timezone + reset hour), not the browser's date.
  const current = useRating(null, !!s)
  const weekAgo = (() => {
    if (!day1 || !current.data) return null
    const [y, m, d] = current.data.day.split('-').map(Number)
    const w = iso(new Date(y, m - 1, d - 7))
    return w > day1 ? w : null // only once the Player is older than a week
  })()
  const at = tab === 'day1' ? day1 : tab === 'week' ? weekAgo : null
  const rating = useRating(at, !!s)
  const base = useRating(day1, !!day1) // ▲ deltas are measured from Day 1

  if (!s) return <p className="p-6 font-mono text-text-dim">[Loading…]</p>
  const r = rating.data
  const tabs: [Tab, string, boolean][] = [
    ['current', 'Current rating', true],
    ['day1', 'Day 1 rating', !!day1],
    ['week', '7 days ago', !!weekAgo],
  ]

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-5">
      <header className="flex items-center gap-3">
        <h1 className="font-display text-4xl font-extrabold tracking-tight">Your Rating</h1>
        <RankBadge rank={s.hunter_rank} />
      </header>

      <div className="flex gap-2 overflow-x-auto p-1" role="tablist">
        {tabs
          .filter(([, , enabled]) => enabled)
          .map(([key, label]) => (
            <button
              key={key}
              role="tab"
              aria-selected={tab === key}
              onClick={() => {
                buzz(8)
                setTab(key)
              }}
              className={`chip press shrink-0 ${tab === key ? 'is-active' : ''}`}
            >
              {label}
            </button>
          ))}
      </div>

      {r && (
        <section className="card overflow-hidden p-0">
          <div className="flex items-stretch">
            <div className="level-slab">
              <CountUp value={r.level} className="font-display text-6xl leading-none font-black" />
              <span className="mt-1 text-xs font-extrabold tracking-[0.2em]">LEVEL</span>
            </div>
            <div className="m-3 ml-0 flex flex-1 flex-col items-end justify-center rounded-xl border border-border bg-bg/50 px-4">
              <CountUp value={r.total_xp} className="font-display text-4xl font-black" />
              <span className="text-sm text-text-dim">XP earned</span>
            </div>
          </div>
          <div className="px-4 pt-2 pb-4">
            <XpBar into={r.xp_into_level} toNext={r.xp_to_next} level={r.level} />
          </div>
        </section>
      )}

      {r && (
        <ul className="card divide-y divide-border/70 px-4 py-1">
          {STATS.map(({ key, name, icon, color }) => {
            const value = r.stats[key] ?? 0
            const delta = base.data && tab !== 'day1' ? value - (base.data.stats[key] ?? 0) : 0
            const expanded = open === key
            return (
              <li key={key}>
                <button
                  onClick={() => {
                    buzz(8)
                    setOpen(expanded ? null : key)
                  }}
                  aria-expanded={expanded}
                  className="press flex min-h-16 w-full items-center gap-3 text-left"
                >
                  <FontAwesomeIcon icon={icon} className={`w-6 text-xl ${color}`} />
                  <span className="flex-1 text-lg font-semibold">{name}</span>
                  {delta > 0 && (
                    <span className="text-sm font-bold text-success tabular">
                      <FontAwesomeIcon icon={faCaretUp} /> {delta}
                    </span>
                  )}
                  <CountUp
                    value={value}
                    className="w-20 text-right font-display text-4xl font-black"
                  />
                  <FontAwesomeIcon
                    icon={faChevronDown}
                    className={`text-xs text-text-dim transition-transform ${expanded ? 'rotate-180' : ''}`}
                  />
                </button>
                <AnimatePresence initial={false}>
                  {expanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <StatDetail stat={key} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </li>
            )
          })}
        </ul>
      )}

      {r && (
        <section className="card p-4">
          <h2 className="mb-2 font-display text-lg font-extrabold">Stat shape</h2>
          <StatRadar values={r.stats} />
        </section>
      )}

      <Insights level={s.level} rank={s.hunter_rank} />

      {s.penalty_quests.length > 0 && (
        <section className="card border-danger/60 p-4">
          <h2 className="mb-3 font-display text-lg font-extrabold text-danger">Penalty Zone</h2>
          <ul className="flex flex-col gap-3">
            {s.penalty_quests.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center gap-3">
                <p className="flex-1">{p.description}</p>
                <button
                  onClick={() => clearPenalty.mutate(p.id)}
                  disabled={clearPenalty.isPending}
                  className="chip press border-danger text-danger"
                >
                  Survived
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {s.max_strikes !== null && (
        <section className={`card p-4 ${s.rank_sealed ? 'border-danger/60' : ''}`}>
          <h2 className="text-sm text-text-dim">Strikes</h2>
          <p className="font-display text-4xl font-black tabular">
            {s.strikes} / {s.max_strikes}
          </p>
          {s.rank_sealed && (
            <p className="mt-1 font-mono text-sm text-danger">[Hunter Rank sealed.]</p>
          )}
        </section>
      )}
    </div>
  )
}
