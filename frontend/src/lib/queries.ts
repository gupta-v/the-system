import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { usePushNotices } from './notices'
import { api, call, type Schemas, type Today } from './api'

export const keys = { today: ['today'], status: ['status'] } as const

export const useToday = () =>
  useQuery({ queryKey: keys.today, queryFn: () => call(api.GET('/days/today')) })

export const useStatus = () =>
  useQuery({ queryKey: keys.status, queryFn: () => call(api.GET('/me/status')) })

/** After any quest change: swap in the new quest, show notices, refresh the Status Window. */
function useQuestUpdate() {
  const qc = useQueryClient()
  const push = usePushNotices()
  return (update: Schemas['QuestUpdateOut']) => {
    qc.setQueryData<Today>(keys.today, (old) => old && { ...old, quest: update.quest, notices: [] })
    push(update.notices)
    void qc.invalidateQueries({ queryKey: keys.status })
  }
}

export function useLogGoal() {
  const onUpdate = useQuestUpdate()
  return useMutation({
    mutationFn: ({ id, progress }: { id: string; progress: number }) =>
      call(
        api.PATCH('/days/today/goals/{goal_log_id}', {
          params: { path: { goal_log_id: id } },
          body: { progress },
        }),
      ),
    onSuccess: onUpdate,
  })
}

export function useClearAll() {
  const onUpdate = useQuestUpdate()
  return useMutation({
    mutationFn: () => call(api.POST('/days/today/clear-all')),
    onSuccess: onUpdate,
  })
}

export function useRecoveryPotion() {
  const onUpdate = useQuestUpdate()
  return useMutation({
    mutationFn: () => call(api.POST('/days/today/recovery-potion')),
    onSuccess: onUpdate,
  })
}

export function useClearPenalty() {
  const qc = useQueryClient()
  const push = usePushNotices()
  return useMutation({
    mutationFn: (id: string) =>
      call(
        api.POST('/penalty-quests/{penalty_id}/clear', { params: { path: { penalty_id: id } } }),
      ),
    onSuccess: (res) => {
      push(res.notices)
      void qc.invalidateQueries({ queryKey: keys.status })
    },
  })
}

export const useHistory = (from: string, to: string) =>
  useQuery({
    queryKey: ['history', from, to],
    queryFn: () => call(api.GET('/days', { params: { query: { from, to } } })),
  })

export const useRating = (at: string | null, enabled = true) =>
  useQuery({
    queryKey: ['rating', at],
    queryFn: () => call(api.GET('/me/rating', { params: { query: at ? { at } : {} } })),
    enabled,
  })

export const useStatDetail = (stat: string | null) =>
  useQuery({
    queryKey: ['stat', stat],
    queryFn: () =>
      call(
        api.GET('/me/stats/{stat}', {
          params: { path: { stat: stat as Schemas['Stat'] } },
        }),
      ),
    enabled: stat !== null,
  })

export const useDay = (day: string | null) =>
  useQuery({
    queryKey: ['day', day],
    queryFn: () => call(api.GET('/days/{day}', { params: { path: { day: day! } } })),
    enabled: day !== null,
  })

export const useXpJourney = () =>
  useQuery({ queryKey: ['xp-journey'], queryFn: () => call(api.GET('/me/xp-journey')) })

export const useInsights = () =>
  useQuery({ queryKey: ['insights'], queryFn: () => call(api.GET('/me/insights')) })

export const useRules = () =>
  useQuery({ queryKey: ['rules'], queryFn: () => call(api.GET('/rules')), staleTime: Infinity })
