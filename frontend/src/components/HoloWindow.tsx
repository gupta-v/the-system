import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faExclamation, faXmark } from '@fortawesome/free-solid-svg-icons'
import { motion } from 'motion/react'
import type { ReactNode } from 'react'

/** Filigree corner (anime System notice). Drawn for the top-left; rotated for the others. */
function Corner({ className }: { className: string }) {
  return (
    <svg
      viewBox="0 0 60 60"
      className={`pointer-events-none absolute size-12 text-xp drop-shadow-[0_0_4px_rgb(255_138_61_/_0.6)] sm:size-14 ${className}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M2 58 V8 Q2 2 8 2 H58" strokeWidth="2.2" />
      <path d="M8 46 C8 26 14 14 30 10 C40 8 46 12 46 18 C46 24 40 26 36 22 C33 19 35 15 39 16" />
      <path d="M14 52 C12 40 16 30 24 26 C30 23 34 26 33 30 C32 33 28 33 27 30" />
      <path d="M46 8 C34 9 22 14 16 26" />
      <circle cx="8" cy="8" r="2.2" fill="currentColor" />
      <path d="M2 30 C6 28 8 24 8 20 M30 2 C28 6 24 8 20 8" />
    </svg>
  )
}

/** Crest at the top-centre of the frame. */
function Crest() {
  return (
    <svg
      viewBox="0 0 120 28"
      className="pointer-events-none absolute -top-3.5 left-1/2 h-7 w-28 -translate-x-1/2 text-xp drop-shadow-[0_0_4px_rgb(255_138_61_/_0.6)]"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M60 2 C54 10 50 14 42 16 C34 18 30 14 32 10 C34 7 38 8 37 11" />
      <path d="M60 2 C66 10 70 14 78 16 C86 18 90 14 88 10 C86 7 82 8 83 11" />
      <path d="M60 6 V22 M52 22 C56 18 64 18 68 22" />
      <path d="M4 24 H44 M76 24 H116" strokeWidth="1" />
      <circle cx="60" cy="24" r="2.5" fill="currentColor" />
    </svg>
  )
}

// Fixed pseudo-random scratches so they don't jump between renders.
const SCRATCHES = Array.from({ length: 26 }, (_, i) => {
  const r = (n: number) => (((Math.sin(i * 12.9898 + n * 78.233) * 43758.5453) % 1) + 1) % 1
  const x = r(1) * 100
  const y = r(2) * 100
  const len = 6 + r(3) * 22
  const a = (-35 + r(4) * 25) * (Math.PI / 180)
  return {
    x1: x,
    y1: y,
    x2: x + Math.cos(a) * len,
    y2: y + Math.sin(a) * len,
    o: 0.08 + r(5) * 0.18,
  }
})

function Scratches() {
  return (
    <svg
      className="pointer-events-none absolute inset-0 size-full"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      {SCRATCHES.map((s, i) => (
        <line
          key={i}
          x1={s.x1}
          y1={s.y1}
          x2={s.x2}
          y2={s.y2}
          stroke="rgb(255 255 255)"
          strokeOpacity={s.o}
          strokeWidth="0.25"
          vectorEffect="non-scaling-stroke"
        />
      ))}
    </svg>
  )
}

type Props = { title: string; onClose?: () => void; children: ReactNode; className?: string }

/**
 * Holographic System window: ornate corners, crest, scratches, scanlines.
 * Opens sideways like the series: a glowing line draws out from the centre, then the panel unfolds.
 */
export function HoloWindow({ title, onClose, children, className = '' }: Props) {
  return (
    <motion.div
      className={`relative ${className}`}
      initial={{ scaleX: 0, scaleY: 0.012, opacity: 0.6 }}
      animate={{ scaleX: 1, scaleY: 1, opacity: 1 }}
      exit={{ scaleY: 0.012, opacity: 0, transition: { duration: 0.2 } }}
      transition={{
        scaleX: { duration: 0.35, ease: [0.22, 1, 0.36, 1] },
        scaleY: { delay: 0.3, duration: 0.4, ease: [0.22, 1, 0.36, 1] },
      }}
    >
      <div className="holo overflow-hidden">
        <Scratches />
        <div className="relative px-6 pt-8 pb-6 sm:px-10">
          <div className="holo-line" />
          <header className="relative flex items-center justify-center gap-3 py-3">
            <span className="holo-text grid size-8 place-items-center rounded-full border-2 border-xp text-sm text-xp">
              <FontAwesomeIcon icon={faExclamation} />
            </span>
            <h2 className="font-display text-3xl font-black tracking-tight">
              {title}
            </h2>
            {onClose && (
              <button
                onClick={onClose}
                aria-label="Close"
                className="absolute top-1/2 right-0 grid size-11 -translate-y-1/2 place-items-center text-danger/90 hover:text-danger"
              >
                <FontAwesomeIcon icon={faXmark} />
              </button>
            )}
          </header>
          <div className="holo-line mb-5" />
          {children}
        </div>
      </div>
      <Crest />
      <Corner className="-top-2 -left-2" />
      <Corner className="-top-2 -right-2 rotate-90" />
      <Corner className="-right-2 -bottom-2 rotate-180" />
      <Corner className="-bottom-2 -left-2 -rotate-90" />
    </motion.div>
  )
}
