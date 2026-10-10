import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useRef, useState, type ReactNode } from 'react'
import type { Notice } from '../lib/api'
import { PushNotices } from '../lib/notices'
import { SystemWindow } from './SystemWindow'
import { TypedText } from './TypedText'

type Queued = Notice & { key: number }

const DANGER = new Set(['penalty', 'warning', 'penalty_expired'])
const TITLES: Record<string, string> = {
  awakening: 'Awakening',
  quest_arrived: 'Daily Quest',
  quest_complete: 'Quest complete',
  reward: 'Reward',
  rank_up: 'Hunter Rank',
  penalty: 'Penalty zone',
  title_acquired: 'Title',
  warning: 'Warning',
}

function LevelUp({ notice, onClose }: { notice: Queued; onClose: () => void }) {
  return (
    <div className="flex flex-col items-center gap-6 text-center" onClick={onClose}>
      <motion.p
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="font-display text-4xl font-black tracking-tight sm:text-6xl"
      >
        Level up!
      </motion.p>
      <motion.div
        initial={{ scale: 0.3, rotate: -8, opacity: 0 }}
        animate={{ scale: 1, rotate: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 260, damping: 13, delay: 0.15 }}
        className="level-slab min-w-48 py-6 shadow-[6px_6px_0_0_#000]"
      >
        <span className="font-display text-8xl leading-none font-black tabular">
          {String(notice.data?.to)}
        </span>
        <span className="mt-1 text-sm font-extrabold tracking-[0.25em]">LEVEL</span>
      </motion.div>
      <p className="text-text-dim">
        from {String(notice.data?.from)} · <span className="font-semibold text-text">tap to continue</span>
      </p>
    </div>
  )
}

/** Shows System notices one at a time, in order. The backend decides what happened. */
export function NoticeProvider({ children }: { children: ReactNode }) {
  const [queue, setQueue] = useState<Queued[]>([])
  const nextKey = useRef(0)
  const push = useCallback((notices: Notice[]) => {
    if (notices.length === 0) return
    setQueue((q) => [...q, ...notices.map((n) => ({ ...n, key: nextKey.current++ }))])
  }, [])
  const current = queue[0]
  const dismiss = () => setQueue((q) => q.slice(1))
  const danger = current !== undefined && DANGER.has(current.type)

  return (
    <PushNotices.Provider value={push}>
      {children}
      <AnimatePresence mode="wait">
        {current && (
          <motion.div
            key={current.key}
            className={`fixed inset-0 z-50 grid place-items-center p-4 backdrop-blur-sm ${
              current.type === 'level_up'
                ? 'bg-black/85'
                : danger
                  ? 'bg-danger/15'
                  : 'bg-black/60'
            }`}
            initial={{ opacity: 0 }}
            // Penalty: brief, subtle shake (style guide §5: 150 ms).
            animate={danger ? { opacity: 1, x: [0, -6, 6, -4, 4, 0] } : { opacity: 1 }}
            transition={danger ? { x: { duration: 0.15, delay: 0.3 } } : undefined}
            exit={{ opacity: 0 }}
            onClick={dismiss}
            role="dialog"
            aria-modal="true"
            aria-live="assertive"
          >
            {current.type === 'level_up' ? (
              <LevelUp notice={current} onClose={dismiss} />
            ) : (
              <div className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
                <SystemWindow
                  title={TITLES[current.type] ?? 'Notification'}
                  tone={danger ? 'danger' : 'system'}
                  onClose={dismiss}
                >
                  <TypedText
                    text={current.message}
                    className="font-mono text-base leading-relaxed text-text"
                  />
                  {queue.length > 1 && (
                    <p className="mt-4 text-right font-mono text-xs text-text-dim">
                      {queue.length - 1} more
                    </p>
                  )}
                </SystemWindow>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </PushNotices.Provider>
  )
}
