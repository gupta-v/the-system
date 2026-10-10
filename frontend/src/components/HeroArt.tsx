import { useArt } from '../lib/art'

/**
 * Character art bleeding behind the content (ref1/ref2): fixed to the right on desktop,
 * centred behind the top on phones, faded into the background with gradients.
 */
export function HeroArt() {
  const { art } = useArt()
  if (!art) return null
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <img
        src={art.url}
        alt=""
        className="absolute top-0 left-1/2 h-[75vh] w-auto max-w-none -translate-x-1/2 object-cover sm:right-0 sm:left-auto sm:h-full sm:translate-x-0"
        style={{
          opacity: 'var(--art-opacity)',
          maskImage:
            'linear-gradient(to bottom, black 35%, transparent 95%), linear-gradient(to left, black 40%, transparent 100%)',
          maskComposite: 'intersect',
          WebkitMaskComposite: 'source-in',
          WebkitMaskImage:
            'linear-gradient(to bottom, black 35%, transparent 95%), linear-gradient(to left, black 40%, transparent 100%)',
        }}
      />
      {/* Tint so text on top stays readable */}
      <div className="absolute inset-0 bg-gradient-to-r from-bg/90 via-bg/50 to-bg/10" />
      <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-bg to-transparent" />
    </div>
  )
}
