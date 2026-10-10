import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent, type ReactNode } from 'react'
import { api, call, type Schemas } from '../../lib/api'
import { ARTS, NO_ART, setArt, useArt } from '../../lib/art'
import { DIFFICULTIES, DIFFICULTY_LABELS, type Difficulty } from '../../lib/difficulty'
import { buzz } from '../../lib/haptics'
import { keys } from '../../lib/queries'
import { WeekSummary } from './WeeklyPlan'

type Settings = Schemas['SettingsOut']
type Sex = 'male' | 'female' | 'other'

const input =
  'min-h-11 w-full rounded-xl border border-border bg-bg px-3 text-text outline-none focus:border-accent'

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-semibold text-text-dim">{label}</span>
      {children}
      {hint && <span className="text-xs text-text-dim">{hint}</span>}
    </label>
  )
}

const numOrNull = (v: string) => (v.trim() === '' ? null : Number(v))

function ProfileForm({ settings }: { settings: Settings }) {
  const qc = useQueryClient()
  const [name, setName] = useState(settings.display_name)
  const [sex, setSex] = useState<Sex | null>((settings.sex as Sex | null) ?? null)
  const [birth, setBirth] = useState(settings.birth_date ?? '')
  const [height, setHeight] = useState(settings.height_cm?.toString() ?? '')
  const [weight, setWeight] = useState(settings.weight_kg?.toString() ?? '')
  const [difficulty, setDifficulty] = useState<Difficulty>(settings.difficulty)
  const [resetHour, setResetHour] = useState(settings.reset_hour)
  const [saved, setSaved] = useState(false)

  const save = useMutation({
    mutationFn: () => {
      const body: Schemas['SettingsIn'] = {
        display_name: name,
        sex,
        birth_date: birth || null,
        height_cm: numOrNull(height),
        weight_kg: numOrNull(weight),
        reset_hour: resetHour,
      }
      // Only send difficulty when it changed: the System allows one change per week.
      if (difficulty !== settings.difficulty) body.difficulty = difficulty
      return call(api.PATCH('/me/settings', { body }))
    },
    onSuccess: (next) => {
      buzz([10, 40, 18])
      qc.setQueryData(['settings'], next)
      void qc.invalidateQueries({ queryKey: keys.status })
      setSaved(true)
    },
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setSaved(false)
    save.mutate()
  }

  const bmi = height && weight ? Number(weight) / (Number(height) / 100) ** 2 : null

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <section className="card flex flex-col gap-4 p-5">
        <h2 className="font-display text-xl font-extrabold">Hunter profile</h2>
        <Field label="Hunter name">
          <input
            className={input}
            required
            maxLength={64}
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>

        <Field label="Sex">
          <div className="flex flex-wrap gap-2 p-1">
            {(['male', 'female', 'other'] as const).map((s) => (
              <button
                key={s}
                type="button"
                aria-pressed={sex === s}
                onClick={() => setSex(sex === s ? null : s)}
                className={`chip capitalize ${sex === s ? 'is-active' : ''}`}
              >
                {s}
              </button>
            ))}
          </div>
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field
            label="Date of birth"
            hint={settings.age != null ? `Age ${settings.age}` : undefined}
          >
            <input
              className={input}
              type="date"
              value={birth}
              onChange={(e) => setBirth(e.target.value)}
            />
          </Field>
          <Field label="Height (cm)">
            <input
              className={input}
              type="number"
              inputMode="decimal"
              min={50}
              max={272}
              step="0.1"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
            />
          </Field>
          <Field label="Weight (kg)" hint={bmi ? `BMI ${bmi.toFixed(1)}` : undefined}>
            <input
              className={input}
              type="number"
              inputMode="decimal"
              min={20}
              max={500}
              step="0.1"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
            />
          </Field>
        </div>
      </section>

      <section className="card flex flex-col gap-4 p-5">
        <h2 className="font-display text-xl font-extrabold">The System</h2>
        <Field label="Difficulty" hint="Can be changed once per week.">
          <div className="no-scrollbar flex gap-2 overflow-x-auto p-1 text-sm">
            {DIFFICULTIES.map((d) => (
              <button
                key={d}
                type="button"
                aria-pressed={difficulty === d}
                onClick={() => setDifficulty(d)}
                className={`chip shrink-0 px-3 ${difficulty === d ? 'is-active' : ''}`}
              >
                {DIFFICULTY_LABELS[d]}
              </button>
            ))}
          </div>
        </Field>
        <Field label="Day resets at" hint={`Timezone: ${settings.timezone}`}>
          <select
            className={input}
            value={resetHour}
            onChange={(e) => setResetHour(Number(e.target.value))}
          >
            {Array.from({ length: 24 }, (_, h) => (
              <option key={h} value={h}>
                {String(h).padStart(2, '0')}:00
              </option>
            ))}
          </select>
        </Field>
      </section>

      {save.error && (
        <p role="alert" className="font-mono text-sm text-danger">
          {save.error.message}
        </p>
      )}
      {saved && !save.isPending && (
        <p role="status" className="font-mono text-sm text-success">
          [Status updated.]
        </p>
      )}
      <button className="btn" disabled={save.isPending}>
        Save
      </button>
    </form>
  )
}

function ArtPicker() {
  const { id } = useArt()
  const choices = [...ARTS, { id: NO_ART, label: 'none', url: '' }]
  return (
    <section className="card flex flex-col gap-3 p-5">
      <h2 className="font-display text-xl font-extrabold">Background art</h2>
      <p className="text-xs text-text-dim">
        Add your own images to <code>frontend/src/assets/art/</code> and they appear here. Saved on
        this device.
      </p>
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
        {choices.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => {
              buzz(8)
              setArt(a.id)
            }}
            aria-pressed={id === a.id}
            aria-label={`Background: ${a.label}`}
            className={`press relative aspect-[3/4] overflow-hidden rounded-xl border-2 bg-bg ${
              id === a.id ? 'border-xp' : 'border-border'
            }`}
          >
            {a.url ? (
              <img src={a.url} alt="" className="size-full object-cover" />
            ) : (
              <span className="grid size-full place-items-center text-sm text-text-dim">None</span>
            )}
            <span className="absolute inset-x-0 bottom-0 truncate bg-bg/70 px-1 py-0.5 text-[10px] capitalize">
              {a.label}
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}

export function ProfilePage() {
  const { data, error } = useQuery({
    queryKey: ['settings'],
    queryFn: () => call(api.GET('/me/settings')),
  })
  return (
    <div className="mx-auto flex max-w-xl flex-col gap-5">
      <h1 className="font-display text-4xl font-extrabold tracking-tight">Profile</h1>
      {error && <p className="font-mono text-danger">{error.message}</p>}
      {data ? (
        <ProfileForm settings={data} />
      ) : (
        <p className="font-mono text-text-dim">[Loading…]</p>
      )}
      <WeekSummary />
      <ArtPicker />
    </div>
  )
}
