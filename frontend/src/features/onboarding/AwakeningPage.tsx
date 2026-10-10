import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { usePushNotices } from '../../lib/notices'
import { SystemWindow } from '../../components/SystemWindow'
import { api, call, type Schemas } from '../../lib/api'
import { DIFFICULTIES, DIFFICULTY_LABELS, type Difficulty } from '../../lib/difficulty'
import { keys } from '../../lib/queries'

type Answers = Schemas['AwakeningIn']
type Path = NonNullable<Answers['path']>

const PATHS: Path[] = ['balanced', 'strength', 'endurance', 'scholar']
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const EXTRAS = [
  ['water', 'Water'],
  ['sleep', 'Sleep'],
  ['reading', 'Reading'],
  ['meditation', 'Meditation'],
  ['no_sugar', 'No sugar'],
  ['steps', 'Steps'],
] as const

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={on}
      className={`chip capitalize ${on ? 'is-active' : ''}`}
    >
      {children}
    </button>
  )
}

const toggle = <T,>(list: T[], item: T) =>
  list.includes(item) ? list.filter((x) => x !== item) : [...list, item]

/** Awakening + Regimen interview (regimen.md §2). Every answer has a default. */
export function AwakeningPage() {
  const [path, setPath] = useState<Path>('balanced')
  const [training, setTraining] = useState([0, 2, 4])
  const [recovery, setRecovery] = useState([6])
  const [extras, setExtras] = useState<string[]>(['water', 'sleep'])
  const [difficulty, setDifficulty] = useState<Difficulty>('awakened')
  const navigate = useNavigate()
  const push = usePushNotices()
  const qc = useQueryClient()

  const awaken = useMutation({
    mutationFn: () =>
      call(
        api.POST('/awakening', {
          body: {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            path,
            training_days: training,
            recovery_days: recovery,
            extras,
            difficulty,
          },
        }),
      ),
    onSuccess: (today) => {
      qc.setQueryData(keys.today, { ...today, notices: [] })
      push(today.notices)
      navigate('/', { replace: true })
    },
  })

  // A day is Training, Recovery or Standard; picking one kind removes it from the other.
  const pickTraining = (d: number) => {
    setTraining(toggle(training, d))
    setRecovery(recovery.filter((x) => x !== d))
  }
  const pickRecovery = (d: number) => {
    setRecovery(toggle(recovery, d))
    setTraining(training.filter((x) => x !== d))
  }

  return (
    <main className="mx-auto max-w-xl p-4 pb-16">
      <SystemWindow title="Awakening">
        <p className="mb-6 font-mono text-system">[You have been chosen as a Player.]</p>

        <h2 className="mb-2 text-sm text-text-dim">[Choose your path.]</h2>
        <div className="mb-6 flex flex-wrap gap-2">
          {PATHS.map((p) => (
            <Chip key={p} on={path === p} onClick={() => setPath(p)}>
              {p}
            </Chip>
          ))}
        </div>

        <h2 className="mb-2 text-sm text-text-dim">[Which days will you train?]</h2>
        <div className="mb-6 flex flex-wrap gap-2">
          {DAYS.map((d, i) => (
            <Chip key={d} on={training.includes(i)} onClick={() => pickTraining(i)}>
              {d}
            </Chip>
          ))}
        </div>

        <h2 className="mb-2 text-sm text-text-dim">[Which days will you recover?]</h2>
        <div className="mb-6 flex flex-wrap gap-2">
          {DAYS.map((d, i) => (
            <Chip key={d} on={recovery.includes(i)} onClick={() => pickRecovery(i)}>
              {d}
            </Chip>
          ))}
        </div>

        <h2 className="mb-2 text-sm text-text-dim">[Anything else the System must track?]</h2>
        <div className="mb-6 flex flex-wrap gap-2">
          {EXTRAS.map(([code, label]) => (
            <Chip
              key={code}
              on={extras.includes(code)}
              onClick={() => setExtras(toggle(extras, code))}
            >
              {label}
            </Chip>
          ))}
        </div>

        <h2 className="mb-2 text-sm text-text-dim">[Difficulty]</h2>
        <div className="no-scrollbar mb-8 flex gap-2 overflow-x-auto p-1 text-sm">
          {DIFFICULTIES.map((d) => (
            <Chip key={d} on={difficulty === d} onClick={() => setDifficulty(d)}>
              {DIFFICULTY_LABELS[d]}
            </Chip>
          ))}
        </div>

        {awaken.error && (
          <p role="alert" className="mb-4 font-mono text-sm text-danger">
            {awaken.error.message}
          </p>
        )}
        <button onClick={() => awaken.mutate()} disabled={awaken.isPending} className="btn w-full">
          ACCEPT REGIMEN
        </button>
      </SystemWindow>
    </main>
  )
}
