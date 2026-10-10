import { useEffect, useState } from 'react'

const MS_PER_CHAR = 25 // ui-style-guide §5

/** Types text in like a System message. Reduced motion: shows it at once. */
export function TypedText({ text, className = '' }: { text: string; className?: string }) {
  const instant =
    typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const [shown, setShown] = useState(instant ? text.length : 0)
  useEffect(() => {
    if (instant) return
    const id = setInterval(() => {
      setShown((n) => {
        if (n >= text.length) clearInterval(id)
        return n + 1
      })
    }, MS_PER_CHAR)
    return () => clearInterval(id)
  }, [text, instant])
  return (
    <p className={className} aria-label={text}>
      <span aria-hidden="true">{text.slice(0, shown)}</span>
      {shown < text.length && <span className="animate-pulse text-system">▌</span>}
    </p>
  )
}
