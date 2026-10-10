import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faExclamation } from '@fortawesome/free-solid-svg-icons'
import { useEffect, useState } from 'react'

const DAY = 24 * 3600
const SEGMENTS = 6 // one box per 4 hours

function useSecondsLeft(until: string | undefined) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])
  return until ? Math.max(0, Math.floor((new Date(until).getTime() - now) / 1000)) : 0
}

const pad = (n: number) => String(n).padStart(2, '0')

/**
 * Time to reset as a System notification: the clock, and 6 boxes of 4 hours (XP-bar style).
 * The current box drains smoothly; everything turns red in the last hour.
 */
export function Countdown({ until }: { until: string | undefined }) {
  const s = useSecondsLeft(until)
  const urgent = s < 3600
  const left = (s / DAY) * SEGMENTS
  const time = `${pad(Math.floor(s / 3600))}h ${pad(Math.floor((s % 3600) / 60))}m ${pad(s % 60)}s`
  const tone = urgent ? 'text-danger' : 'text-xp'
  const fillBg = urgent ? 'bg-danger' : 'bg-linear-to-r from-xp to-beige'
  return (
    <section
      role="timer"
      aria-label={`Daily Quest resets in ${time}`}
      className="card flex flex-col gap-3 px-5 py-4 font-mono"
    >
      <div className="flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
        <div>
          <header className={`flex items-center gap-2 ${tone}`}>
            <span
              className={`grid size-6 place-items-center rounded-md text-xs text-bg ${urgent ? 'bg-danger' : 'bg-xp'}`}
            >
              <FontAwesomeIcon icon={faExclamation} />
            </span>
            <h2 className="text-xs font-bold tracking-[0.3em]">
              {urgent ? 'WARNING' : 'NOTIFICATION'}
            </h2>
          </header>
          <p className="mt-1 text-sm text-text-dim">[Daily Quest resets in]</p>
        </div>
        <p className={`text-2xl font-bold tabular ${urgent ? 'text-danger' : 'text-beige'}`}>
          {time}
        </p>
      </div>
      <div className="flex gap-1.5" aria-hidden>
        {Array.from({ length: SEGMENTS }, (_, i) => {
          const fill = Math.min(1, Math.max(0, left - i))
          return (
            <div key={i} className="h-2.5 flex-1 overflow-hidden rounded-[3px] bg-border">
              <div
                className={`h-full rounded-[3px] transition-[width] duration-1000 ease-linear ${fillBg} ${
                  fill > 0 ? 'shadow-[0_0_8px_-2px_var(--color-xp)]' : ''
                }`}
                style={{ width: `${fill * 100}%` }}
              />
            </div>
          )
        })}
      </div>
    </section>
  )
}
