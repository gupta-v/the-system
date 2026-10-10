// Pentagon radar of the five stats (anime Skills screen). Plain SVG, no chart lib.
const ORDER = ['STR', 'AGI', 'PER', 'INT', 'VIT'] as const
const LABELS: Record<string, string> = { STR: 'STR', AGI: 'AGI', PER: 'PER', INT: 'INT', VIT: 'VIT' }
const R = 80
const C = 100

function point(i: number, r: number): [number, number] {
  const a = -Math.PI / 2 + (i * 2 * Math.PI) / ORDER.length
  return [C + r * Math.cos(a), C + r * Math.sin(a)]
}
const poly = (pts: [number, number][]) => pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')

export function StatRadar({ values }: { values: Record<string, number> }) {
  // Scale to the strongest stat plus headroom, so growth is visible from the start.
  const max = Math.max(...ORDER.map((k) => values[k] ?? 0)) * 1.25 || 1
  const shape = ORDER.map((k, i) => point(i, (R * (values[k] ?? 0)) / max))
  return (
    <svg
      viewBox="0 0 200 200"
      className="mx-auto w-full max-w-72 drop-shadow-[0_0_10px_var(--color-glow)]"
      role="img"
      aria-label={`Stats: ${ORDER.map((k) => `${k} ${values[k] ?? 0}`).join(', ')}`}
    >
      {[1, 0.75, 0.5, 0.25].map((f) => (
        <polygon
          key={f}
          points={poly(ORDER.map((_, i) => point(i, R * f)))}
          fill={f === 1 ? 'var(--color-bg-elev)' : 'none'}
          stroke="var(--color-border)"
          strokeWidth={f === 1 ? 2 : 1}
        />
      ))}
      {ORDER.map((_, i) => {
        const [x, y] = point(i, R)
        return <line key={i} x1={C} y1={C} x2={x} y2={y} stroke="var(--color-border)" />
      })}
      <polygon
        points={poly(shape)}
        fill="var(--color-system)"
        fillOpacity="0.35"
        stroke="var(--color-system)"
        strokeWidth="2"
      />
      {ORDER.map((k, i) => {
        const [x, y] = point(i, R + 13)
        return (
          <text
            key={k}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-system font-display text-[10px] font-bold"
          >
            {LABELS[k]}
          </text>
        )
      })}
    </svg>
  )
}
