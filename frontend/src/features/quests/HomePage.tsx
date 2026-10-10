import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCoins,
  faFire,
  faFlask,
  faListCheck,
  faSkull,
  type IconDefinition,
} from '@fortawesome/free-solid-svg-icons'
import { AnimatePresence } from 'motion/react'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router'
import { CountUp } from '../../components/CountUp'
import { Countdown } from '../../components/Countdown'
import { GoalRow, type XpGain } from '../../components/GoalRow'
import { RankBadge } from '../../components/RankBadge'
import { RulesScroll } from '../../components/RulesScroll'
import { XpBar } from '../../components/XpBar'
import { buzz } from '../../lib/haptics'
import { usePushNotices } from '../../lib/notices'
import { useClearAll, useLogGoal, useRecoveryPotion, useStatus, useToday } from '../../lib/queries'

const TONES = {
  xp: 'bg-xp/15 text-xp',
  mint: 'bg-mint/15 text-mint',
  aqua: 'bg-aqua/15 text-aqua',
  beige: 'bg-beige/15 text-beige',
  danger: 'bg-danger/15 text-danger',
}

function StatTile({
  label,
  icon,
  tone,
  children,
}: {
  label: string
  icon: IconDefinition
  tone: keyof typeof TONES
  children: ReactNode
}) {
  return (
    <section className="card flex items-center gap-3 p-4">
      <span
        className={`grid size-11 shrink-0 place-items-center rounded-xl text-lg ${TONES[tone]}`}
      >
        <FontAwesomeIcon icon={icon} />
      </span>
      <div className="min-w-0">
        <h2 className="truncate text-xs text-text-dim">{label}</h2>
        <p className="font-display text-2xl font-black">{children}</p>
      </div>
    </section>
  )
}

// Shown once today's Daily Quest is cleared; one picked at random per visit.
const CLEARED_LINES = [
  '[Daily Quest complete. You grow stronger, Player. Keep it up.]',
  '[The weak stay weak. You did not.]',
  '[Every rep is a step toward S-Rank.]',
  '[Discipline acknowledged. The System is watching.]',
  '[Yesterday you were weaker. Tomorrow you will be stronger.]',
  '[You chose the hard path again today. Arise.]',
  '[Strength is earned one day at a time. Today is earned.]',
  '[Clear the quest. Level up. Repeat.]',
  '[No Penalty Zone today. Well done, Player.]',
  '[The gap between you and the weak grows wider.]',
  '[A Hunter is forged by days like this one.]',
  '[Your limits moved today. Keep pushing them.]',
]
const RECOVERY_LINES = [
  '[Recovery Day cleared. Rest well, Player.]',
  '[Recovery is training too. Restore your strength.]',
  '[A rested Hunter hits harder tomorrow.]',
  '[Muscles grow in rest. Let them.]',
  '[Mana restored. Prepare for the next Gate.]',
  '[Even the Shadow Monarch rests between battles.]',
  '[Recovery Potion earned. Spend it wisely.]',
  '[Calm body, sharp mind. Tomorrow you rise.]',
  '[Rest is not weakness. Skipping it is.]',
  '[The System grants rest to those who earn it.]',
  '[Recover today. Dominate tomorrow.]',
  '[Your strength is rebuilding, Player.]',
]

export function HomePage() {
  const today = useToday()
  const status = useStatus()
  const logGoal = useLogGoal()
  const clearAll = useClearAll()
  const potion = useRecoveryPotion()
  const push = usePushNotices()
  const [gains, setGains] = useState<Record<string, XpGain>>({})
  const gainKey = useRef(0)
  const [params, setParams] = useSearchParams()
  const rulesOpen = params.get('rules') === '1'
  const [roll] = useState(Math.random)

  // Notices from opening the day (quest arrived, day-close penalties) come with /days/today.
  const notices = today.data?.notices
  useEffect(() => {
    if (notices?.length) push(notices)
  }, [notices, push])

  if (!today.data) return <p className="p-6 font-mono text-text-dim">[Loading…]</p>
  const { quest } = today.data
  const s = status.data
  const busy = logGoal.isPending || clearAll.isPending || potion.isPending
  const error = logGoal.error ?? clearAll.error ?? potion.error
  const plan = quest.goals.filter((g) => !g.done)
  const completed = quest.goals.filter((g) => g.done)
  const recovery = quest.day_kind === 'recovery'
  const cleared = quest.goals.length > 0 && plan.length === 0

  const log = (id: string, progress: number) =>
    logGoal.mutate(
      { id, progress },
      {
        onSuccess: (u) =>
          setGains((g) => ({ ...g, [id]: { xp: u.xp_gained, key: gainKey.current++ } })),
      },
    )

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4">
      <AnimatePresence>
        {rulesOpen && <RulesScroll onClose={() => setParams({}, { replace: true })} />}
      </AnimatePresence>
      {/* Hero: who + level (ref2 rating card) */}
      {s && (
        <section className="card overflow-hidden p-0">
          <div className="flex items-stretch">
            <div className="level-slab">
              <CountUp value={s.level} className="font-display text-6xl leading-none font-black" />
              <span className="mt-1 text-xs font-extrabold tracking-[0.2em]">LEVEL</span>
            </div>
            <div className="flex min-w-0 flex-1 items-center gap-3 p-4">
              <div className="min-w-0 flex-1">
                <p className="truncate font-display text-2xl font-extrabold">{s.display_name}</p>
                <p className="text-sm text-text-dim">
                  {s.title ? s.title.name : `Hunter Rank ${s.hunter_rank}`}
                </p>
              </div>
              <RankBadge rank={s.hunter_rank} size="lg" />
            </div>
          </div>
          <div className="px-4 pt-2 pb-4">
            <XpBar into={s.xp_into_level} toNext={s.xp_to_next} level={s.level} />
          </div>
        </section>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Daily Quest" icon={faListCheck} tone="xp">
          <CountUp value={completed.length} />
          <span className="text-text-dim"> / {quest.goals.length}</span>
        </StatTile>
        <StatTile label="Streak" icon={faFire} tone="xp">
          <CountUp value={s?.streak ?? 0} />
        </StatTile>
        <StatTile label="Gold" icon={faCoins} tone="beige">
          <CountUp value={s?.gold ?? 0} />
        </StatTile>
        {s?.max_strikes != null ? (
          <StatTile label="Strikes" icon={faSkull} tone="danger">
            {s.strikes} <span className="text-text-dim">/ {s.max_strikes}</span>
          </StatTile>
        ) : (
          <StatTile label="Recovery Potions" icon={faFlask} tone="mint">
            <CountUp value={s?.recovery_potions ?? 0} />
          </StatTile>
        )}
      </div>

      <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
        <Countdown until={today.data.resets_at} />
        <section className="card p-5">
          <p className="text-center font-mono text-sm text-system">
            [Daily Quest: {quest.title} has arrived.]
          </p>
          <h1 className="mt-1 mb-4 text-center font-display text-3xl font-extrabold tracking-tight">
            Goals
          </h1>

          {quest.goals.length > 0 ? (
            <ul className="flex flex-col gap-2">
              {[...plan, ...completed].map((g) => (
                <GoalRow
                  key={g.id}
                  goal={g}
                  gain={gains[g.id]}
                  disabled={busy}
                  onProgress={(p) => log(g.id, p)}
                />
              ))}
            </ul>
          ) : (
            <p className="font-mono text-text-dim">[No Goals today. Rest.]</p>
          )}
          {quest.goals.length > 0 && (
            <p className="mt-2 text-xs text-text-dim">Tip: swipe a Goal right to complete it.</p>
          )}

          {error && (
            <p role="alert" className="mt-3 font-mono text-sm text-danger">
              {error.message}
            </p>
          )}
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              onClick={() => {
                buzz([10, 40, 18])
                clearAll.mutate()
              }}
              disabled={busy || plan.length === 0}
              className="btn flex-1"
            >
              Clear All
            </button>
            {quest.day_kind === 'training' && (
              <button
                onClick={() => potion.mutate()}
                disabled={busy || s?.recovery_potions === 0}
                className="chip"
              >
                <FontAwesomeIcon icon={faFlask} /> Potion
                {s ? ` (${s.recovery_potions})` : ''}
              </button>
            )}
          </div>

          <p
            className={`mt-5 text-center text-sm ${cleared ? 'font-semibold text-mint' : recovery || quest.day_kind === 'standard' ? 'text-system' : 'text-danger'}`}
          >
            {cleared ? (
              recovery ? (
                RECOVERY_LINES[Math.floor(roll * RECOVERY_LINES.length)]
              ) : (
                CLEARED_LINES[Math.floor(roll * CLEARED_LINES.length)]
              )
            ) : recovery ? (
              '[Recovery Day. Goals are optional. Restore your strength.]'
            ) : quest.day_kind === 'standard' ? (
              '[Standard Day. Keep your Default Routine. No penalty, no XP: Gold for a full clear.]'
            ) : (
              <>
                WARNING: Failure to complete the daily quest will result in an appropriate{' '}
                <span className="font-bold">penalty</span>.
              </>
            )}
          </p>
        </section>
      </div>
    </div>
  )
}
