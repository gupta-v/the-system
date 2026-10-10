import { motion } from 'motion/react'

const SEGMENTS = 24

/** Segmented XP bar (ref2): chunky orange segments, next one outlined, fills left→right. */
export function XpBar({ into, toNext, level }: { into: number; toNext: number; level: number }) {
  const filled = Math.floor((into / toNext) * SEGMENTS)
  return (
    <div>
      <div
        className="flex gap-1"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={toNext}
        aria-valuenow={into}
        aria-label="Experience"
      >
        {Array.from({ length: SEGMENTS }, (_, i) => (
          <motion.div
            key={i}
            className={`h-4 flex-1 rounded-[3px] ${i < filled ? 'shadow-[0_0_8px_-2px_var(--color-xp)]' : ''} ${i === filled ? 'border-2 border-text' : ''}`}
            initial={false}
            animate={{
              backgroundColor: i < filled ? 'var(--color-xp)' : 'var(--color-border)',
            }}
            transition={{ delay: i * 0.025 }}
          />
        ))}
      </div>
      <p className="mt-2 text-center text-sm text-text-dim tabular">
        <span className="font-bold text-text">{toNext - into} XP</span> to Lvl {level + 1}
      </p>
    </div>
  )
}
