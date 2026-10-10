import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPlus, faTrash } from '@fortawesome/free-solid-svg-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { api, call, type Schemas } from '../../lib/api'
import { buzz } from '../../lib/haptics'
import { keys } from '../../lib/queries'

type Goal = Schemas['GoalOut']
type Stat = Schemas['Stat']
type Kind = Schemas['GoalKind']

const STATS: Stat[] = ['STR', 'VIT', 'AGI', 'INT', 'PER']
const STAT_COLOR: Record<Stat, string> = {
  STR: 'text-stat-str',
  VIT: 'text-stat-vit',
  AGI: 'text-stat-agi',
  INT: 'text-stat-int',
  PER: 'text-stat-per',
}
const input =
  'min-h-11 w-full rounded-xl border border-border bg-bg px-3 text-text outline-none focus:border-accent'

/** Create (no `goal`) or edit a Goal. Kind is fixed after creation (logged history depends on it). */
function GoalForm({ goal, onDone }: { goal?: Goal; onDone: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState(goal?.name ?? '')
  const [stat, setStat] = useState<Stat>(goal?.stat ?? 'STR')
  const [kind, setKind] = useState<Kind>(goal?.kind ?? 'numeric')
  const [target, setTarget] = useState(String(goal?.target ?? 10))
  const [unit, setUnit] = useState(goal?.unit ?? '')
  const [scales, setScales] = useState(goal?.scales_with_rank ?? false)
  const [sets, setSets] = useState(goal?.sets?.toString() ?? '')
  const numeric = kind === 'numeric'

  const save = useMutation({
    mutationFn: () => {
      const fields = {
        name,
        stat,
        target: numeric ? Number(target) : 1,
        unit: numeric && unit.trim() ? unit.trim() : null,
        scales_with_rank: numeric && scales,
        sets: sets ? Number(sets) : null,
      }
      return goal
        ? call(
            api.PATCH('/goals/{goal_id}', { params: { path: { goal_id: goal.id } }, body: fields }),
          )
        : call(api.POST('/goals', { body: { ...fields, kind } }))
    },
    onSuccess: () => {
      buzz([10, 40, 18])
      void qc.invalidateQueries({ queryKey: ['goals'] })
      void qc.invalidateQueries({ queryKey: keys.today })
      onDone()
    },
  })

  const submit = (e: FormEvent) => {
    e.preventDefault()
    save.mutate()
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3 rounded-xl border border-border p-3">
      <input
        className={input}
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Goal name, e.g. Push-ups"
        maxLength={80}
        required
        aria-label="Goal name"
      />
      <div className="flex flex-wrap gap-2" role="group" aria-label="Stat">
        {STATS.map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={stat === s}
            onClick={() => setStat(s)}
            className={`chip shrink-0 px-3 text-sm ${stat === s ? 'is-active' : STAT_COLOR[s]}`}
          >
            {s}
          </button>
        ))}
      </div>
      {!goal && (
        <div className="flex gap-2" role="group" aria-label="Goal type">
          {(
            [
              ['numeric', 'Count / amount'],
              ['check', 'Done / not done'],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              type="button"
              aria-pressed={kind === k}
              onClick={() => setKind(k)}
              className={`chip text-sm ${kind === k ? 'is-active' : ''}`}
            >
              {label}
            </button>
          ))}
        </div>
      )}
      {numeric && (
        <>
          <div className="flex gap-2">
            <input
              className={input}
              type="number"
              inputMode="decimal"
              min={0}
              step="any"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              required
              aria-label="Target"
            />
            <input
              className={`${input} max-w-28`}
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              placeholder="unit (km, min)"
              maxLength={16}
              aria-label="Unit"
            />
          </div>
          <label className="flex min-h-11 items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={scales}
              onChange={(e) => setScales(e.target.checked)}
              className="size-5 accent-[var(--color-xp)]"
            />
            Scale with Hunter Rank (target is the A-Rank amount)
          </label>
        </>
      )}
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-semibold text-text-dim">Sets (optional)</span>
        <input
          className={input}
          type="number"
          inputMode="numeric"
          min={2}
          max={20}
          step={1}
          value={sets}
          onChange={(e) => setSets(e.target.value)}
          placeholder="e.g. 4: tap the box once per set"
          aria-label="Sets"
        />
      </label>
      {save.error && (
        <p role="alert" className="font-mono text-sm text-danger">
          {save.error.message}
        </p>
      )}
      <div className="flex gap-2">
        <button className="btn flex-1" disabled={save.isPending || !name.trim()}>
          {goal ? 'Save Goal' : 'Add Goal'}
        </button>
        <button type="button" className="chip" onClick={onDone}>
          Cancel
        </button>
      </div>
    </form>
  )
}

/** All Goals: add, edit, archive. Archived Goals leave future Daily Quests; history keeps them. */
export function GoalEditor() {
  const qc = useQueryClient()
  const goals = useQuery({ queryKey: ['goals'], queryFn: () => call(api.GET('/goals')) })
  const [editing, setEditing] = useState<string | 'new' | null>(null)
  const archive = useMutation({
    mutationFn: (id: string) =>
      call(api.DELETE('/goals/{goal_id}', { params: { path: { goal_id: id } } })),
    onSuccess: () => {
      buzz(12)
      void qc.invalidateQueries({ queryKey: ['goals'] })
      void qc.invalidateQueries({ queryKey: keys.today })
    },
  })

  const current = goals.data?.find((g) => g.id === editing)

  return (
    <section className="card flex flex-col gap-3 p-5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="font-display text-xl font-extrabold">Goals</h2>
          <p className="text-xs text-text-dim">
            Tap a Goal to edit it. Applies from the next quest.
          </p>
        </div>
        <button
          className={`chip press shrink-0 ${editing === 'new' ? 'is-active' : ''}`}
          onClick={() => setEditing(editing === 'new' ? null : 'new')}
        >
          <FontAwesomeIcon icon={faPlus} /> Add
        </button>
      </div>

      <div className="no-scrollbar -mx-5 flex gap-2 overflow-x-auto px-5 py-1">
        {goals.data?.map((g) => (
          <button
            key={g.id}
            type="button"
            aria-pressed={editing === g.id}
            onClick={() => setEditing(editing === g.id ? null : g.id)}
            className={`chip shrink-0 px-3 text-sm ${editing === g.id ? 'is-active' : ''}`}
          >
            <span
              className={`text-[10px] font-black ${editing === g.id ? '' : STAT_COLOR[g.stat]}`}
            >
              {g.stat}
            </span>
            {g.name}
          </button>
        ))}
      </div>

      {editing === 'new' && <GoalForm onDone={() => setEditing(null)} />}
      {current && (
        <>
          <GoalForm key={current.id} goal={current} onDone={() => setEditing(null)} />
          <button
            className="chip press text-danger"
            disabled={archive.isPending}
            onClick={() => {
              if (confirm(`Archive "${current.name}"? It leaves future Daily Quests.`))
                archive.mutate(current.id, { onSuccess: () => setEditing(null) })
            }}
          >
            <FontAwesomeIcon icon={faTrash} /> Archive Goal
          </button>
        </>
      )}

      {archive.error && (
        <p role="alert" className="font-mono text-sm text-danger">
          {archive.error.message}
        </p>
      )}
    </section>
  )
}
