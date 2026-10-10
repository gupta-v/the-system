import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck, faMinus, faPlus, faRotateLeft } from '@fortawesome/free-solid-svg-icons'
import { AnimatePresence, motion, useMotionValue, useTransform } from 'motion/react'
import { useRef } from 'react'
import { buzz } from '../lib/haptics'
import type { GoalLog } from '../lib/api'

export type XpGain = { xp: number; key: number }

type Props = {
  goal: GoalLog
  disabled: boolean
  gain?: XpGain
  onProgress: (progress: number) => void
}

const SWIPE = 90 // px to commit a swipe
const HOLD_MS = 500 // press this long on the box to clear a Goal with sets
const fmt = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1))

/**
 * Goal row. Tap the box (or swipe right) = done as planned; swipe left = undo.
 * Numeric Goals also get ±10% steps. Goals with sets: each tap fills one set, hold the box to clear.
 */
export function GoalRow({ goal, disabled, gain, onProgress }: Props) {
  const step = Math.max(1, Math.round(goal.target / 10))
  const numeric = goal.kind === 'numeric'
  const sets = goal.sets ?? 0
  const setsDone = sets ? Math.round((goal.progress / goal.target) * sets) : 0
  const x = useMotionValue(0)
  const doneHint = useTransform(x, [0, SWIPE], [0, 1])
  const undoHint = useTransform(x, [-SWIPE, 0], [1, 0])
  const set = (p: number) => {
    buzz(p >= goal.target ? [10, 40, 18] : 8)
    onProgress(p)
  }
  // "reps" is implied by a bare number (Push-ups × 20).
  const unit = goal.unit && goal.unit !== 'reps' ? ` ${goal.unit}` : ''
  const counter = sets
    ? `${setsDone}/${sets} sets`
    : numeric
      ? `${fmt(goal.progress)}/${fmt(goal.target)}${unit}`
      : `${goal.done ? 1 : 0}/1`
  const pct = Math.min(100, (goal.progress / goal.target) * 100)
  const hold = useRef<{ timer?: number; fired: boolean }>({ fired: false })
  const startHold = () => {
    hold.current.fired = false
    hold.current.timer = window.setTimeout(() => {
      hold.current.fired = true
      if (goal.progress > 0) set(0)
    }, HOLD_MS)
  }
  const endHold = () => window.clearTimeout(hold.current.timer)
  const tapBox = () => {
    if (hold.current.fired) return // the hold already cleared it
    if (!sets) return set(goal.done ? 0 : goal.target)
    if (setsDone >= sets) return buzz([20, 30, 20]) // full: hold to clear
    set(setsDone + 1 >= sets ? goal.target : (goal.target * (setsDone + 1)) / sets)
  }

  return (
    <li className="relative overflow-hidden rounded-xl">
      {/* Swipe reveals */}
      <motion.div
        style={{ opacity: doneHint }}
        className="absolute inset-0 flex items-center bg-success/20 pl-5 text-success"
        aria-hidden="true"
      >
        <FontAwesomeIcon icon={faCheck} />
      </motion.div>
      <motion.div
        style={{ opacity: undoHint }}
        className="absolute inset-0 flex items-center justify-end bg-danger/15 pr-5 text-danger"
        aria-hidden="true"
      >
        <FontAwesomeIcon icon={faRotateLeft} />
      </motion.div>

      <motion.div
        drag={disabled ? false : 'x'}
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.6}
        dragSnapToOrigin
        style={{ x }}
        onDragEnd={(_, info) => {
          if (info.offset.x > SWIPE && !goal.done) set(goal.target)
          else if (info.offset.x < -SWIPE && goal.progress > 0) set(0)
        }}
        className={`relative flex touch-pan-y items-center gap-2 border border-border bg-panel px-3 py-2 ${
          goal.done ? 'opacity-60' : ''
        } rounded-xl`}
      >
        {/* Partial progress fill */}
        <div
          className="pointer-events-none absolute inset-y-0 left-0 rounded-xl bg-xp/10 transition-[width] duration-500"
          style={{ width: `${goal.done ? 0 : pct}%` }}
          aria-hidden="true"
        />
        <div className="relative min-w-0 flex-1">
          <p className={`font-semibold ${goal.done ? 'line-through' : ''}`}>
            {goal.name}
            {numeric && (
              <span className="font-normal text-text-dim">
                {' '}
                × {fmt(goal.target)}
                {unit}
              </span>
            )}
          </p>
          <p className="font-mono text-xs text-text-dim">{goal.stat}</p>
        </div>

        {numeric && !sets && !goal.done && (
          <span className="relative flex items-center">
            <button
              disabled={disabled || goal.progress <= 0}
              onClick={() => set(Math.max(0, goal.progress - step))}
              aria-label={`${goal.name}: decrease`}
              className="press size-11 rounded-lg text-text-dim hover:text-text disabled:opacity-30"
            >
              <FontAwesomeIcon icon={faMinus} size="xs" />
            </button>
            <button
              disabled={disabled}
              onClick={() => set(goal.progress + step)}
              aria-label={`${goal.name}: increase`}
              className="press size-11 rounded-lg text-text-dim hover:text-text disabled:opacity-30"
            >
              <FontAwesomeIcon icon={faPlus} size="xs" />
            </button>
          </span>
        )}

        <span className="relative font-display text-lg font-extrabold whitespace-nowrap tabular">
          {counter}
        </span>

        <button
          disabled={disabled}
          onClick={tapBox}
          onPointerDown={sets ? startHold : undefined}
          onPointerUp={endHold}
          onPointerLeave={endHold}
          onPointerCancel={endHold}
          onContextMenu={(e) => sets && e.preventDefault()}
          aria-pressed={goal.done}
          aria-label={
            sets
              ? `${goal.name}: ${setsDone} of ${sets} sets. Tap to add a set, hold to clear.`
              : `${goal.name}: ${goal.done ? 'mark not done' : 'mark done'}`
          }
          className="press relative grid size-11 shrink-0 place-items-center"
        >
          <span
            className={`relative grid size-7 place-items-center overflow-hidden rounded-lg border-2 text-sm transition ${
              goal.done
                ? 'border-success bg-success text-bg'
                : 'border-text-dim text-transparent hover:border-text'
            }`}
          >
            {sets > 0 && !goal.done && (
              <span
                className="absolute inset-x-0 bottom-0 bg-xp/70 transition-[height] duration-300"
                style={{ height: `${(setsDone / sets) * 100}%` }}
                aria-hidden
              />
            )}
            <FontAwesomeIcon icon={faCheck} className="relative" />
          </span>
        </button>
      </motion.div>

      <AnimatePresence>
        {gain && gain.xp !== 0 && (
          <motion.span
            key={gain.key}
            initial={{ opacity: 0, y: 4, scale: 0.8 }}
            animate={{ opacity: [0, 1, 1, 0], y: -24, scale: 1 }}
            transition={{ duration: 1.4 }}
            className={`pointer-events-none absolute top-0 right-16 font-display text-base font-black ${
              gain.xp > 0 ? 'text-xp' : 'text-danger'
            }`}
            aria-hidden="true"
          >
            {gain.xp > 0 ? '+' : ''}
            {gain.xp} XP
          </motion.span>
        )}
      </AnimatePresence>
    </li>
  )
}
