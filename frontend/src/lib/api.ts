import createClient from 'openapi-fetch'
import type { components, paths } from './api-types'

// Types are generated from FastAPI: `pnpm gen:api` (backend must be running).
export type Schemas = components['schemas']
export type Notice = Schemas['Notice']
export type Today = Schemas['TodayOut']
export type Quest = Schemas['DailyQuestOut']
export type GoalLog = Schemas['GoalLogOut']
export type Status = Schemas['StatusOut']

export const api = createClient<paths>({ baseUrl: '/api', credentials: 'include' })

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** Unwrap an openapi-fetch result; throw ApiError with the System's message on failure. */
export async function call<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await request
  if (response.ok) return data as T
  const detail = (error as { detail?: unknown } | undefined)?.detail
  // FastAPI validation errors are a list; domain errors are a "[System message]" string.
  const message = typeof detail === 'string' ? detail : '[Invalid input.]'
  throw new ApiError(response.status, message)
}
