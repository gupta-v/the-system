import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck, faPlus, faTrash } from '@fortawesome/free-solid-svg-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'
import { api, call, type Schemas } from '../../lib/api'
import { buzz } from '../../lib/haptics'
import { keys } from '../../lib/queries'

type Regimen = Schemas['RegimenOut']
type Goal = Schemas['GoalOut']
type Kind = Schemas['DayKind']
type Scope = 'this_week' | 'from_now_on'
/** A Routine being edited. `key` is stable across renames; the week refers to Routines by key. */
type Routine = {
  key: string
  name: string
  goals: { goal_id: string; target_override: number | null }[]
}

const MAX_PER_DAY = 2
/** Runs on every Standard day (a day with no Routines picked). Can't be renamed or deleted. */
const DEFAULT = 'Default Routine'
// shortcut: matched by name (Goals have no preset code); renaming Water/Sleep unlocks them.
const isLocked = (g: Goal) => g.name === 'Water' || g.name.startsWith('Sleep')

const toRoutine = (d: { name: string; goals: Routine['goals'] }): Routine => ({
  key: d.name,
  name: d.name,
  goals: d.goals.map((g) => ({ goal_id: g.goal_id, target_override: g.target_override })),
})

/** Default Routine first (always present, always holding Water + Sleep), then the rest. */
function startRoutines(regimen: Regimen, goals: Goal[]): Routine[] {
  const saved = regimen.day_types.find((d) => d.name === DEFAULT)
  const first = toRoutine(saved ?? { name: DEFAULT, goals: [] })
  for (const g of goals.filter(isLocked))
    if (!first.goals.some((x) => x.goal_id === g.id))
      first.goals.push({ goal_id: g.id, target_override: null })
  return [first, ...regimen.day_types.filter((d) => d.name !== DEFAULT).map(toRoutine)]
}
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const KINDS: Kind[] = ['training', 'standard', 'recovery']
const KIND_STYLE: Record<Kind, string> = {
  training: 'border-xp bg-xp/20 text-text',
  standard: 'border-beige/70 bg-beige/10 text-beige',
  recovery: 'border-mint bg-mint/15 text-mint',
}
const input =
  'min-h-11 w-full rounded-xl border border-border bg-bg px-3 font-semibold text-text outline-none focus:border-accent'
const row = 'no-scrollbar -mx-5 flex gap-2 overflow-x-auto px-5 py-1'

const useRegimen = () =>
  useQuery({ queryKey: ['regimen'], queryFn: () => call(api.GET('/regimen')) })

/** Profile: the week's day types, read-only. Changes happen on the Plan page. */
export function WeekSummary() {
  const regimen = useRegimen()
  return (
    <section className="card flex flex-col gap-4 p-5">
      <h2 className="font-display text-xl font-extrabold">Weekly plan</h2>
      {regimen.error && <p className="font-mono text-danger">{regimen.error.message}</p>}
      {regimen.data && (
        <div className="grid grid-cols-7 gap-1.5">
          {regimen.data.day_kinds.map((k, i) => (
            <div
              key={i}
              className={`flex min-h-16 flex-col items-center justify-center gap-1 rounded-xl border-2 px-0.5 ${KIND_STYLE[k]}`}
            >
              <span className="text-xs font-bold">{WEEKDAYS[i]}</span>
              <span className="text-[10px] capitalize">{k}</span>
            </div>
          ))}
        </div>
      )}
      <Link to="/plan" className="chip press">
        Customize your plan
      </Link>
    </section>
  )
}

function Editor({
  regimen,
  goals,
  goalSection,
}: {
  regimen: Regimen
  goals: Goal[]
  goalSection: ReactNode
}) {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [routines, setRoutines] = useState<Routine[]>(() => startRoutines(regimen, goals))
  const [kinds, setKinds] = useState<Kind[]>(regimen.day_kinds)
  // A day's Routines are always shown in Routine order (Routine 2 above Routine 3).
  const order = (day: string[], keys: string[]) =>
    [...day].sort((a, b) => keys.indexOf(a) - keys.indexOf(b))
  const [week, setWeek] = useState<string[][]>(() =>
    regimen.week.map((d) =>
      order(
        d,
        routines.map((t) => t.key),
      ),
    ),
  )
  const [day, setDay] = useState(0) // weekday whose Routines are being picked
  const [scope, setScope] = useState<Scope>('from_now_on')
  const [changed, setChanged] = useState(false)
  const byKey = Object.fromEntries(routines.map((r) => [r.key, r]))
  const active = new Set(goals.map((g) => g.id))

  const edit = () => {
    setChanged(true)
    buzz(8)
  }

  const save = useMutation({
    mutationFn: () =>
      call(
        api.PUT('/regimen', {
          body: {
            day_types: routines.map(({ name, goals }) => ({
              name: name.trim(),
              // Archived Goals can't be saved back, so drop them here.
              goals: goals.filter((g) => active.has(g.goal_id)),
            })),
            day_kinds: kinds,
            week: week.map((d) => d.map((k) => byKey[k].name.trim())),
            scope,
          },
        }),
      ),
    onSuccess: (next) => {
      buzz([10, 40, 18])
      qc.setQueryData(['regimen'], next)
      void qc.invalidateQueries({ queryKey: keys.today })
      navigate('/profile')
    },
  })

  const cycleKind = (i: number) => {
    edit()
    const next = KINDS[(KINDS.indexOf(kinds[i]) + 1) % KINDS.length]
    setKinds(kinds.map((k, j) => (j === i ? next : k)))
    // Standard days have no Routines.
    if (next === 'standard') setWeek(week.map((d, j) => (j === i ? [] : d)))
  }
  const toggleDay = (key: string) => {
    const routinesToday = week[day]
    if (!routinesToday.includes(key) && routinesToday.length >= MAX_PER_DAY)
      return buzz([20, 30, 20])
    edit()
    const next = routinesToday.includes(key)
      ? routinesToday.filter((k) => k !== key)
      : order(
          [...routinesToday, key],
          routines.map((r) => r.key),
        )
    setWeek(week.map((d, j) => (j === day ? next : d)))
    // A day with nothing picked is a Standard day.
    if (next.length === 0) setKinds(kinds.map((k, j) => (j === day ? 'standard' : k)))
  }
  const patch = (key: string, change: Partial<Routine>) => {
    edit()
    setRoutines(routines.map((r) => (r.key === key ? { ...r, ...change } : r)))
  }
  const toggleGoal = (r: Routine, g: Goal) =>
    r.key === DEFAULT && isLocked(g)
      ? buzz([20, 30, 20])
      : patch(r.key, {
          goals: r.goals.some((x) => x.goal_id === g.id)
            ? r.goals.filter((x) => x.goal_id !== g.id)
            : [...r.goals, { goal_id: g.id, target_override: null }],
        })
  const addRoutine = () => {
    edit()
    let n = routines.length + 1
    while (routines.some((r) => r.name === `Routine ${n}`)) n++
    setRoutines([...routines, { key: crypto.randomUUID(), name: `Routine ${n}`, goals: [] }])
  }
  const removeRoutine = (key: string) => {
    edit()
    setRoutines(routines.filter((r) => r.key !== key))
    setWeek(week.map((d) => d.filter((k) => k !== key)))
  }

  const names = routines.map((r) => r.name.trim().toLowerCase())
  const bareTraining = kinds.findIndex((k, i) => k === 'training' && week[i].length === 0)
  const problem = names.some((n) => !n)
    ? 'Every Routine needs a name.'
    : new Set(names).size !== names.length
      ? 'Routine names must be different.'
      : bareTraining >= 0
        ? `${WEEKDAYS[bareTraining]} is a Training day: add a Routine.`
        : kinds.every((k) => k === 'recovery')
          ? 'Keep at least one Training or Standard day.'
          : null

  return (
    <>
      <section className="card flex flex-col gap-4 p-5">
        <div>
          <h2 className="font-display text-xl font-extrabold">Weekly plan</h2>
          <p className="text-xs text-text-dim">
            Tap a day to switch Training / Standard / Recovery. Tap its Routines to change them.
          </p>
        </div>

        <div className={row}>
          {kinds.map((k, i) => (
            <div key={i} className="flex w-24 shrink-0 flex-col gap-1.5">
              <button
                type="button"
                onClick={() => cycleKind(i)}
                aria-label={`${WEEKDAYS[i]}: ${k} day. Tap to switch.`}
                className={`press flex min-h-14 flex-col items-center justify-center rounded-xl border-2 ${KIND_STYLE[k]}`}
              >
                <span className="text-sm font-bold">{WEEKDAYS[i]}</span>
                <span className="text-[11px] capitalize">{k}</span>
              </button>
              <button
                type="button"
                onClick={() => setDay(i)}
                disabled={k === 'standard'}
                aria-pressed={day === i}
                aria-label={`${WEEKDAYS[i]} Routines: ${week[i].map((r) => byKey[r].name).join(', ') || 'none'}`}
                className={`press flex min-h-16 flex-col items-center justify-center gap-0.5 rounded-xl border-2 px-1 text-center text-[11px] leading-tight ${
                  day === i ? 'border-text' : 'border-border'
                } ${k === 'training' && week[i].length === 0 ? 'text-danger' : 'text-text-dim'}`}
              >
                {week[i].length
                  ? week[i].map((r) => (
                      <span key={r} className="line-clamp-1 font-semibold text-text">
                        {byKey[r].name}
                      </span>
                    ))
                  : k === 'training'
                    ? 'Add a Routine'
                    : k === 'standard'
                      ? DEFAULT
                      : 'None'}
              </button>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-1.5">
          <p className="text-xs font-bold text-text-dim">
            {kinds[day] === 'standard'
              ? `${WEEKDAYS[day]} is a Standard day: it runs the ${DEFAULT}.`
              : `${WEEKDAYS[day]}: pick up to ${MAX_PER_DAY} Routines`}
          </p>
          <div className={`${row} ${kinds[day] === 'standard' ? 'hidden' : ''}`}>
            {routines.map((r) => {
              const on = week[day].includes(r.key)
              return (
                <button
                  key={r.key}
                  type="button"
                  aria-pressed={on}
                  onClick={() => toggleDay(r.key)}
                  className={`chip shrink-0 px-3 text-sm ${on ? 'is-active' : ''}`}
                >
                  {r.name || '…'}
                </button>
              )
            })}
          </div>
        </div>
      </section>

      {goalSection}

      <section className="card flex flex-col gap-4 p-5">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="font-display text-xl font-extrabold">Routines</h2>
            <p className="text-xs text-text-dim">
              A Routine is a set of Goals. Tap to add or remove.
            </p>
          </div>
          <button className="chip press shrink-0" onClick={addRoutine}>
            <FontAwesomeIcon icon={faPlus} /> Add
          </button>
        </div>

        <div className={`${row} items-start`}>
          {routines.map((r) => (
            <div
              key={r.key}
              className={`flex w-56 shrink-0 flex-col gap-2 rounded-xl border border-border p-3 ${
                r.key === DEFAULT ? 'bg-bg-elev' : ''
              }`}
            >
              {r.key === DEFAULT ? (
                <div className="flex min-h-11 flex-col justify-center px-1">
                  <p className="font-semibold">{DEFAULT}</p>
                  <p className="text-xs text-text-dim">Runs on Standard days</p>
                </div>
              ) : (
                <div className="flex items-center gap-1">
                  <input
                    className={input}
                    value={r.name}
                    maxLength={64}
                    onChange={(e) => patch(r.key, { name: e.target.value })}
                    aria-label="Routine name"
                  />
                  <button
                    aria-label={`Delete ${r.name}`}
                    className="grid size-11 shrink-0 place-items-center text-text-dim hover:text-danger"
                    onClick={() => {
                      if (confirm(`Delete "${r.name}"? It's removed from every day.`))
                        removeRoutine(r.key)
                    }}
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </button>
                </div>
              )}
              <ul className="flex flex-col gap-1" aria-label={`${r.name} Goals`}>
                {goals.map((g) => {
                  const on = r.goals.some((x) => x.goal_id === g.id)
                  const locked = r.key === DEFAULT && isLocked(g)
                  return (
                    <li key={g.id}>
                      <button
                        type="button"
                        aria-pressed={on}
                        aria-disabled={locked}
                        title={locked ? 'Always in the Default Routine' : undefined}
                        onClick={() => toggleGoal(r, g)}
                        className={`press flex min-h-11 w-full items-center gap-2 rounded-lg px-2 text-left text-sm ${
                          on ? 'bg-xp/15 font-semibold text-text' : 'text-text-dim'
                        }`}
                      >
                        <span
                          className={`grid size-5 shrink-0 place-items-center rounded border text-[10px] ${on ? 'border-xp bg-xp text-bg' : 'border-border'}`}
                        >
                          {on && <FontAwesomeIcon icon={faCheck} />}
                        </span>
                        <span className="truncate">{g.name}</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="card sticky bottom-3 z-10 flex flex-col gap-3 p-4">
        <div className="flex flex-wrap gap-2 p-1">
          {(
            [
              ['from_now_on', 'From now on'],
              ['this_week', 'This week only'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-pressed={scope === key}
              onClick={() => setScope(key)}
              className={`chip ${scope === key ? 'is-active' : ''}`}
            >
              {label}
            </button>
          ))}
        </div>
        {(problem || save.error) && (
          <p role="alert" className="font-mono text-sm text-danger">
            {problem ?? save.error?.message}
          </p>
        )}
        <button
          className="btn"
          disabled={!changed || !!problem || save.isPending}
          onClick={() => save.mutate()}
        >
          Save plan
        </button>
      </section>
    </>
  )
}

/** Plan page: the week (day types + Routines), the Goals (`goalSection`) and the Routines. */
export function WeeklyPlan({ goalSection }: { goalSection: ReactNode }) {
  const regimen = useRegimen()
  const goals = useQuery({ queryKey: ['goals'], queryFn: () => call(api.GET('/goals')) })
  if (regimen.error) return <p className="font-mono text-danger">{regimen.error.message}</p>
  if (!regimen.data || !goals.data) return <p className="font-mono text-text-dim">[Loading…]</p>
  // Remount when the saved Regimen changes so the form starts from it. Goal edits don't remount,
  // so a new Goal can be added to a Routine without losing unsaved changes.
  return (
    <Editor
      key={JSON.stringify(regimen.data)}
      regimen={regimen.data}
      goals={goals.data}
      goalSection={goalSection}
    />
  )
}
