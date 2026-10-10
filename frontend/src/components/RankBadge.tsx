const RANKS = new Set(['F', 'E', 'D', 'C', 'B', 'A', 'S'])

/** Hunter Rank letter in a glowing hex frame; colour per rank from the theme tokens. */
export function RankBadge({ rank, size = 'md' }: { rank: string; size?: 'md' | 'lg' }) {
  const color = `var(--color-rank-${RANKS.has(rank) ? rank.toLowerCase() : 'f'})`
  const box = size === 'lg' ? 'size-16 text-3xl' : 'size-11 text-xl'
  return (
    <div
      role="img"
      aria-label={`Hunter Rank ${rank}`}
      className={`relative grid ${box} shrink-0 place-items-center font-display ${rank === 'S' ? 'animate-pulse' : ''}`}
      style={{ color, filter: `drop-shadow(0 0 6px ${color})` }}
    >
      <svg viewBox="0 0 100 100" className="absolute inset-0 size-full" aria-hidden="true">
        <polygon
          points="25,3 75,3 97,50 75,97 25,97 3,50"
          fill="currentColor"
          fillOpacity="0.15"
          stroke="currentColor"
          strokeWidth="5"
        />
      </svg>
      <span className="relative">{rank}</span>
    </div>
  )
}
