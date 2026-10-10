import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faArrowDown,
  faArrowTrendUp,
  faBolt,
  faCoins,
  faCrown,
  faFlask,
  faSkull,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons'
import { useState } from 'react'
import { CountUp } from '../../components/CountUp'
import type { Schemas } from '../../lib/api'
import { useXpJourney } from '../../lib/queries'

type Day = Schemas['XpJourneyDayOut']

const PAGE = 14
const STATUS: Record<string, { label: string; dot: string }> = {
  cleared: { label: 'Cleared', dot: 'bg-success' },
  passed: { label: 'Passed', dot: 'bg-xp' },
  failed: { label: 'Failed', dot: 'bg-danger' },
  recovery: { label: 'Recovery', dot: 'bg-system' },
  open: { label: 'In progress', dot: 'bg-text' },
}

const fmtDay = (iso: string) =>
  new Date(`${iso}T00:00`).toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  })

function Tag({
  icon,
  tone,
  label,
  children,
}: {
  icon: IconDefinition
  tone: string
  label?: string // screen-reader/hover name when the text is just a number
  children?: string
}) {
  return (
    <span
      title={label}
      aria-label={label && [children, label].filter(Boolean).join(' ')}
      className={`inline-flex items-center gap-1 rounded-lg px-2 py-0.5 text-xs font-bold ${tone}`}
    >
      <FontAwesomeIcon icon={icon} />
      {children}
    </span>
  )
}

function Entry({ d }: { d: Day }) {
  const s = d.status ? STATUS[d.status] : null
  return (
    <li className="relative pl-7">
      {/* timeline node */}
      <span
        className={`absolute top-1.5 left-[5px] size-3 rounded-full ring-4 ring-bg-elev ${s?.dot ?? 'bg-border'}`}
        aria-hidden="true"
      />
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <p className="font-semibold">
          {fmtDay(d.day)}
          <span className="font-normal text-text-dim">
            {' · '}
            {d.quest_title ?? 'No Daily Quest'}
            {s ? ` · ${s.label}` : ''}
            {d.completion != null && d.status !== 'open'
              ? ` ${Math.round(d.completion * 100)}%`
              : ''}
          </span>
        </p>
        <p
          className={`font-display text-lg font-black tabular ${d.xp > 0 ? 'text-xp' : d.xp < 0 ? 'text-danger' : 'text-text-dim'}`}
        >
          {d.xp > 0 ? '+' : ''}
          {d.xp} XP
        </p>
      </div>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {d.level_up && (
          <Tag icon={faArrowTrendUp} tone="flex-row-reverse bg-xp text-bg" label={`${d.level}`}>
            Level
          </Tag>
        )}
        {d.level_down && (
          <Tag
            icon={faArrowDown}
            tone="flex-row-reverse bg-danger text-bg"
            label={`${d.level} (dropped)`}
          >
            Level
          </Tag>
        )}
        {d.potion_earned && (
          <Tag icon={faFlask} tone="bg-mint/15 text-mint" label="Recovery Potion">
            +1
          </Tag>
        )}
        {d.potion_used && (
          <Tag icon={faFlask} tone="bg-system/15 text-system" label="Recovery Potion used">
            −1
          </Tag>
        )}
        {d.xp_penalty < 0 && (
          <Tag icon={faSkull} tone="bg-danger/15 text-danger">
            {`Penalty Zone ${d.xp_penalty} XP`}
          </Tag>
        )}
        {d.gold !== 0 && (
          <Tag icon={faCoins} tone="bg-panel text-text-dim" label="Gold">
            {`${d.gold > 0 ? '+' : ''}${d.gold}`}
          </Tag>
        )}
      </div>
    </li>
  )
}

/** XP Journey: summary + a day-by-day log (newest first) of XP, penalties, potions, level-ups. */
export function XpJourney() {
  const { data, error } = useXpJourney()
  const [shown, setShown] = useState(PAGE)
  if (error) return <p className="font-mono text-sm text-danger">{error.message}</p>
  if (!data) return <p className="font-mono text-sm text-text-dim">[Loading…]</p>
  const days = data.days
  const last = days[days.length - 1]
  const levelsGained = days.filter((d) => d.level_up).length
  const lost = days.reduce((sum, d) => sum + Math.min(0, d.xp_penalty), 0)
  const potions = days.filter((d) => d.potion_used).length
  const log = [...days].reverse()

  return (
    <section className="card p-5">
      <h2 className="font-display text-2xl font-extrabold tracking-tight">XP Journey</h2>
      <p className="mb-4 text-sm text-text-dim">
        Since Day 1 · {days.length} {days.length === 1 ? 'day' : 'days'}
      </p>

      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <p className="text-xs text-text-dim">Total XP</p>
          <p className="font-display text-2xl font-black">
            <FontAwesomeIcon icon={faBolt} className="text-xp" /> <CountUp value={last.total_xp} />
          </p>
        </div>
        <div>
          <p className="text-xs text-text-dim">Level-ups</p>
          <p className="font-display text-2xl font-black">
            <FontAwesomeIcon icon={faCrown} className="text-xp" /> <CountUp value={levelsGained} />
          </p>
        </div>
        <div>
          <p className="text-xs text-text-dim">XP lost</p>
          <p className={`font-display text-2xl font-black ${lost < 0 ? 'text-danger' : ''}`}>
            <FontAwesomeIcon icon={faSkull} className={lost < 0 ? '' : 'text-xp'} />{' '}
            <CountUp value={lost} />
          </p>
        </div>
        <div>
          <p className="text-xs text-text-dim">Potions used</p>
          <p className="font-display text-2xl font-black">
            <FontAwesomeIcon icon={faFlask} className="text-xp" /> <CountUp value={potions} />
          </p>
        </div>
      </div>

      <ol className="relative flex flex-col gap-4 before:absolute before:top-2 before:bottom-2 before:left-[10px] before:w-0.5 before:bg-border">
        {log.slice(0, shown).map((d) => (
          <Entry key={d.day} d={d} />
        ))}
      </ol>
      {shown < log.length && (
        <button className="chip mt-4 w-full" onClick={() => setShown(shown + PAGE)}>
          Show older days ({log.length - shown})
        </button>
      )}
    </section>
  )
}
