import { animate, useMotionValue, useTransform, motion } from 'motion/react'
import { useEffect } from 'react'

/** Number that counts from its previous value to the new one (ref2 count-up). */
export function CountUp({ value, className = '' }: { value: number; className?: string }) {
  const mv = useMotionValue(value)
  const text = useTransform(mv, (v) => Math.round(v).toLocaleString())
  useEffect(() => {
    const controls = animate(mv, value, { duration: 0.8, ease: 'easeOut' })
    return () => controls.stop()
  }, [mv, value])
  return (
    <motion.span className={`tabular ${className}`} aria-label={String(value)}>
      {text}
    </motion.span>
  )
}
