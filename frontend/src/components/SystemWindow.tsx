import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faXmark } from '@fortawesome/free-solid-svg-icons'
import { motion } from 'motion/react'
import type { ReactNode } from 'react'

type Props = {
  title?: string
  tone?: 'system' | 'danger'
  children: ReactNode
  onClose?: () => void
  className?: string
}

/** Card panel (ref2): heavy title, optional close. Pops in with a short spring. */
export function SystemWindow({ title, tone = 'system', children, onClose, className = '' }: Props) {
  const danger = tone === 'danger'
  return (
    <motion.section
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 320, damping: 26 }}
      className={`card p-5 sm:p-6 ${danger ? 'border-danger/60' : ''} ${className}`}
    >
      {(title || onClose) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          {title && (
            <h2
              className={`font-display text-2xl font-extrabold tracking-tight ${danger ? 'text-danger' : ''}`}
            >
              {title}
            </h2>
          )}
          {onClose && (
            <button
              onClick={onClose}
              aria-label="Close"
              className="chip press ml-auto size-11 p-0"
            >
              <FontAwesomeIcon icon={faXmark} />
            </button>
          )}
        </header>
      )}
      {children}
    </motion.section>
  )
}
