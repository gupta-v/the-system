import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCalendarCheck,
  faCheckDouble,
  faFire,
  faFlask,
  faGaugeHigh,
  faTrophy,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons'
import { CountUp } from '../../components/CountUp'
import { RankBadge } from '../../components/RankBadge'
import type { Schemas } from '../../lib/api'
import { useInsights, useRules } from '../../lib/queries'

type Insights = Schemas['InsightsOut']

const pct = (v: number | null | undefined) => (v == null ? '—' : `${Math.round(v * 100)}%`)
const eta = (days: number | null | undefined) =>
  days == null ? 'no pace yet' : days === 0 ? 'now' : `~${days} day${days === 1 ? '' : 's'}`

/** F → S ladder with the current rank lit, plus ETAs at the recent XP pace. */
function RankJourney({ level, rank, ins }: { level: number; rank: string; ins: Insights }) {
  const rules = useRules()
  const ranks = rules.data?.ranks ?? []
  const at = ranks.findIndex((k) => k.rank === rank)
  return (
    <section className="card p-4">
      <h2 className="mb-3 font-display text-lg font-extrabold">Rank journey</h2>
      <ol className="flex items-center justify-between gap-1">
        {ranks.map((k, i) => (
          <li
            key={k.rank}
            className={`flex flex-1 flex-col items-center gap-1 ${i > at ? 'opacity-35' : ''}`}
          >
            <RankBadge rank={k.rank} />
            <span className="text-[10px] text-text-dim tabular">Lv {k.min_level}</span>
          </li>
        ))}
      </ol>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <p>
          <span className="block text-xs text-text-dim">Level {level + 1}</span>
          <span className="font-semibold">{eta(ins.next_level_eta_days)}</span>
        </p>
        <p>
          <span className="block text-xs text-text-dim">
            {ins.next_rank ? `${ins.next_rank}-Rank (Lv ${ins.next_rank_level})` : 'Top tier'}
          </span>
          <span className="font-semibold">
            {ins.next_rank ? eta(ins.next_rank_eta_days) : 'S-Rank reached'}
          </span>
        </p>
      </div>
      <p className="mt-2 text-xs text-text-dim">
        At your pace: <b className="text-xp">{ins.xp_per_day} XP</b>/day (last 14 days)
      </p>
    </section>
  )
}

const HEAT: Record<string, string> = {
  cleared: 'bg-mint',
  passed: 'bg-xp/70',
  failed: 'bg-danger',
  recovery: 'bg-aqua/50',
  open: 'border border-text-dim',
}

/** Last 12 weeks, one cell per game day, columns start on Monday. */
function Heatmap({ ins }: { ins: Insights }) {
  const first = ins.heatmap[0]?.day
  const [y, m, d] = (first ?? '2000-01-03').split('-').map(Number)
  const pad = (new Date(y, m - 1, d).getDay() + 6) % 7 // Monday = 0
  return (
    <section className="card p-4">
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="font-display text-lg font-extrabold">Clear rate</h2>
        <p className="text-xs text-text-dim tabular">
          7d <b className="text-text">{pct(ins.clear_rate_7d)}</b> · 30d{' '}
          <b className="text-text">{pct(ins.clear_rate_30d)}</b> · all{' '}
          <b className="text-text">{pct(ins.clear_rate_all)}</b>
        </p>
      </div>
      <div className="grid grid-flow-col grid-rows-7 gap-1">
        {Array.from({ length: pad }, (_, i) => (
          <span key={`pad${i}`} />
        ))}
        {ins.heatmap.map((h) => (
          <span
            key={h.day}
            title={`${h.day}${h.status ? ` · ${h.status}` : ''}`}
            className={`aspect-square rounded-[3px] ${h.status ? HEAT[h.status] : 'bg-border/50'}`}
          />
        ))}
      </div>
      <p className="mt-3 flex flex-wrap gap-3 text-xs text-text-dim">
        {Object.entries(HEAT).map(([k, cls]) => (
          <span key={k} className="flex items-center gap-1 capitalize">
            <span className={`size-2.5 rounded-[2px] ${cls}`} /> {k}
          </span>
        ))}
      </p>
    </section>
  )
}

function Record({
  icon,
  label,
  value,
  sub,
}: {
  icon: IconDefinition
  label: string
  value: number
  sub?: string
}) {
  return (
    <div className="flex items-center gap-3">
      <FontAwesomeIcon icon={icon} className="w-5 text-xp" />
      <div className="min-w-0">
        <p className="text-xs text-text-dim">{label}</p>
        <p className="font-display text-xl font-black">
          <CountUp value={value} />
          {sub && <span className="ml-1 text-xs font-normal text-text-dim">{sub}</span>}
        </p>
      </div>
    </div>
  )
}

function Records({ ins }: { ins: Insights }) {
  return (
    <section className="card p-4">
      <h2 className="mb-3 font-display text-lg font-extrabold">Records</h2>
      <div className="grid grid-cols-2 gap-4">
        <Record icon={faFire} label="Best streak" value={ins.best_streak} sub="days" />
        <Record
          icon={faTrophy}
          label="Best day"
          value={ins.best_day_xp}
          sub={ins.best_day ? `XP · ${ins.best_day.slice(5)}` : 'XP'}
        />
        <Record icon={faCheckDouble} label="Goals done" value={ins.goals_done} />
        <Record icon={faCalendarCheck} label="Days Awakened" value={ins.days_awakened} />
        <Record icon={faGaugeHigh} label="Current streak" value={ins.current_streak} sub="days" />
        <Record icon={faFlask} label="Potions used" value={ins.potions_used} />
      </div>
    </section>
  )
}

export function Insights({ level, rank }: { level: number; rank: string }) {
  const { data } = useInsights()
  if (!data) return null
  return (
    <>
      <RankJourney level={level} rank={rank} ins={data} />
      <Heatmap ins={data} />
      <Records ins={data} />
    </>
  )
}
