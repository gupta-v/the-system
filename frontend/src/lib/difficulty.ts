import type { components } from './api-types'

export type Difficulty = components['schemas']['Difficulty']

/** Display names for the difficulty levels, easiest first. */
export const DIFFICULTY_LABELS: Record<Difficulty, string> = {
  awakened: 'Awakened',
  elite: 'Elite',
  national: 'National',
  reawakened: 'Reawakened',
  monarch: 'Monarch',
}

export const DIFFICULTIES = Object.keys(DIFFICULTY_LABELS) as Difficulty[]
