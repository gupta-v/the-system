import { useSyncExternalStore } from 'react'

/**
 * Background art. Every image in src/assets/art/ is picked up automatically
 * (drop a .png/.jpg/.webp/.svg there and it shows in Profile → Background art).
 * shortcut: art is bundled with the app, not uploaded per user; move to backend storage for public release.
 */
const files = import.meta.glob('../assets/art/*.{png,jpg,jpeg,webp,svg}', {
  eager: true,
  import: 'default',
}) as Record<string, string>

export type Art = { id: string; label: string; url: string }

export const ARTS: Art[] = Object.entries(files)
  .map(([path, url]) => {
    const id = path.split('/').pop()!.replace(/\.\w+$/, '')
    return { id, label: id.replace(/[-_]/g, ' '), url }
  })
  // Your own images first (the first one is the default); the bundled silhouette is the fallback.
  .sort((a, b) =>
    a.id === 'shadow-hunter' ? 1 : b.id === 'shadow-hunter' ? -1 : a.id.localeCompare(b.id),
  )

const KEY = 'the-system.art'
const NONE = 'none'
const listeners = new Set<() => void>()

function read(): string {
  try {
    return localStorage.getItem(KEY) ?? ARTS[0]?.id ?? NONE
  } catch {
    return ARTS[0]?.id ?? NONE
  }
}

/** Per-device preference (localStorage); falls back to the default art when storage is blocked. */
export function setArt(id: string) {
  try {
    localStorage.setItem(KEY, id)
  } catch {
    // storage unavailable: choice lasts until reload
  }
  current = id
  listeners.forEach((l) => l())
}

let current = read()

export function useArt(): { id: string; art: Art | undefined } {
  const id = useSyncExternalStore(
    (l) => {
      listeners.add(l)
      return () => listeners.delete(l)
    },
    () => current,
  )
  return { id, art: ARTS.find((a) => a.id === id) }
}

export const NO_ART = NONE
