import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck, faChevronLeft, faChevronRight, faXmark } from '@fortawesome/free-solid-svg-icons'
import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'
import { SystemWindow } from '../../components/SystemWindow'
import type { Schemas } from '../../lib/api'
import { buzz } from '../../lib/haptics'
import { useDay, useHistory } from '../../lib/queries'
import { XpJourney } from './XpJourney'

type Day = Schemas['HistoryDayOut']

const iso = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function cellStyle(day: Day | undefined): string {
  if (!day) return 'border-border/40 text-text-dim/50'
  switch (day.status) {
    case 'cleared':
      return 'border-success bg-success/25 text-text shadow-[0_0_10px_-3px_var(--color-success)]'
    case 'passed':
      return 'border-accent/60 bg-accent/15 text-text'
    case 'failed':
      return 'border-danger/70 bg-danger/15 text-danger'
    case 'recovery':
      return 'border-aqua/60 bg-aqua/10 text-aqua'
    default: // open (today)
      return 'border-system text-text'
  }
}

const LEGEND: [string, string][] = [
  ['cleared', 'Cleared'],
  ['passed', 'Passed'],
  ['failed', 'Failed'],
  ['recovery', 'Recovery'],
]

const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1))

/** One day's Daily Quest, read-only. */
function DayDetail({ day, onClose }: { day: string; onClose: () => void }) {
  const { data, error } = useDay(day)
  const label = new Date(`${day}T00:00`).toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  return (
    <section className="card mt-4 p-4">
      <header className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-text-dim">{label}</p>
          {data && (
            <h3 className="font-display text-2xl font-extrabold">
              {data.title}{' '}
              <span className="text-base font-semibold text-text-dim capitalize">
                · {data.status} · {Math.round(data.completion * 100)}%
                {data.potion_used ? ' · Potion used' : ''}
              </span>
            </h3>
          )}
        </div>
        <button onClick={onClose} aria-label="Close day" className="chip press size-11 p-0">
          <FontAwesomeIcon icon={faXmark} />
        </button>
      </header>
      {error && <p className="font-mono text-sm text-danger">{error.message}</p>}
      {!data && !error && <p className="font-mono text-sm text-text-dim">[Loading…]</p>}
      {data && data.goals.length === 0 && (
        <p className="font-mono text-sm text-text-dim">[No Goals this day.]</p>
      )}
      {data && data.goals.length > 0 && (
        <ul className="flex flex-col gap-2">
          {data.goals.map((g) => (
            <li
              key={g.id}
              className="flex items-center gap-3 rounded-xl border border-border bg-panel px-3 py-2"
            >
              <FontAwesomeIcon
                icon={g.done ? faCheck : faXmark}
                className={g.done ? 'text-success' : 'text-danger'}
              />
              <span className="flex-1 font-semibold">{g.name}</span>
              <span className="font-mono text-xs text-text-dim">{g.stat}</span>
              <span className="font-display font-extrabold tabular">
                {g.kind === 'numeric'
                  ? `${fmt(g.progress)}/${fmt(g.target)}${g.unit && g.unit !== 'reps' ? ` ${g.unit}` : ''}`
                  : `${g.done ? 1 : 0}/1`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

/** Month calendar of Daily Quest results (ref4/ref5). Tap a day to see its Goals. */
export function HistoryPage() {
  const [month, setMonth] = useState(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), 1)
  })
  const first = month
  const last = new Date(month.getFullYear(), month.getMonth() + 1, 0)
  const { data, error } = useHistory(iso(first), iso(last))
  const byDay = new Map((data ?? []).map((d) => [d.day, d]))

  const lead = (first.getDay() + 6) % 7 // Monday-first grid
  const cells = [
    ...Array.from({ length: lead }, () => null),
    ...Array.from(
      { length: last.getDate() },
      (_, i) => new Date(month.getFullYear(), month.getMonth(), i + 1),
    ),
  ]
  const [selected, setSelected] = useState<string | null>(null)
  const shift = (n: number) => {
    setSelected(null)
    setMonth(new Date(month.getFullYear(), month.getMonth() + n, 1))
  }
  const days = data ?? []
  const closed = days.filter((d) => d.status !== 'open' && d.status !== 'recovery')
  const clearRate = closed.length
    ? Math.round((closed.filter((d) => d.status === 'cleared').length / closed.length) * 100)
    : null

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5">
      <SystemWindow title="History">
        <div className="mb-4 flex items-center justify-between">
          <button
            onClick={() => shift(-1)}
            aria-label="Previous month"
            className="chip press size-11 p-0"
          >
            <FontAwesomeIcon icon={faChevronLeft} />
          </button>
          <div className="text-center">
            <p className="font-display text-lg">
              {month.toLocaleString(undefined, { month: 'long', year: 'numeric' })}
            </p>
            {clearRate !== null && (
              <p className="font-mono text-xs text-text-dim">[Clear rate {clearRate}%]</p>
            )}
          </div>
          <button
            onClick={() => shift(1)}
            aria-label="Next month"
            className="chip press size-11 p-0"
          >
            <FontAwesomeIcon icon={faChevronRight} />
          </button>
        </div>

        {error && <p className="mb-3 font-mono text-sm text-danger">{error.message}</p>}

        <div className="grid grid-cols-7 gap-1.5 sm:gap-2">
          {WEEKDAYS.map((w) => (
            <p key={w} className="text-center font-mono text-xs text-text-dim">
              {w}
            </p>
          ))}
          {cells.map((date, i) => {
            if (!date) return <div key={`pad-${i}`} />
            const key = iso(date)
            const day = byDay.get(key)
            const cell = `flex aspect-square flex-col justify-between rounded border p-1 sm:p-2 ${cellStyle(day)}`
            const body = (
              <>
                <span className="font-mono text-xs">{date.getDate()}</span>
                {day && day.status !== 'open' && (
                  <span className="hidden text-right font-mono text-[10px] sm:block">
                    {Math.round(day.completion * 100)}%
                  </span>
                )}
              </>
            )
            if (!day)
              return (
                <div key={key} className={cell}>
                  {body}
                </div>
              )
            return (
              <button
                key={key}
                onClick={() => {
                  buzz(8)
                  setSelected(selected === key ? null : key)
                }}
                aria-pressed={selected === key}
                aria-label={`${key}: ${day.title}, ${day.status}, ${Math.round(day.completion * 100)}%`}
                className={`press text-left ${cell} ${selected === key ? 'ring-2 ring-xp' : ''}`}
              >
                {body}
              </button>
            )
          })}
        </div>

        <AnimatePresence>
          {selected && (
            <motion.div
              key={selected}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <DayDetail day={selected} onClose={() => setSelected(null)} />
            </motion.div>
          )}
        </AnimatePresence>

        <ul className="mt-4 flex flex-wrap gap-3 font-mono text-xs text-text-dim">
          {LEGEND.map(([status, label]) => (
            <li key={status} className="flex items-center gap-1.5">
              <span
                className={`inline-block size-3 rounded-sm border ${cellStyle({ status } as Day)}`}
              />
              {label}
            </li>
          ))}
        </ul>
      </SystemWindow>
      <XpJourney />
    </div>
  )
}
