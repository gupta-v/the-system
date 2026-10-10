/** Tiny bar chart of daily values (stat XP per day). Plain SVG. */
export function Sparkline({ values, label }: { values: number[]; label: string }) {
  const max = Math.max(1, ...values)
  const w = 100 / values.length
  return (
    <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="h-12 w-full" role="img" aria-label={label}>
      <line x1="0" y1="29.5" x2="100" y2="29.5" stroke="var(--color-border)" strokeWidth="0.5" />
      {values.map((v, i) => {
        const h = (v / max) * 28
        return (
          <rect
            key={i}
            x={i * w + w * 0.15}
            y={29.5 - h}
            width={w * 0.7}
            height={h}
            fill={i === values.length - 1 ? 'var(--color-xp)' : 'var(--color-system)'}
            opacity={v ? 0.9 : 0}
          />
        )
      })}
    </svg>
  )
}
