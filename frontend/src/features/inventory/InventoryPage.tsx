import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCoins, faCrown, faFlask } from '@fortawesome/free-solid-svg-icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CountUp } from '../../components/CountUp'
import { api, call } from '../../lib/api'
import { buzz } from '../../lib/haptics'
import { keys, useRecoveryPotion, useRules, useStatus, useToday } from '../../lib/queries'

/** Inventory: what the Player holds. Recovery Potions, Gold, earned Titles. */
export function InventoryPage() {
  const status = useStatus()
  const today = useToday()
  const rules = useRules()
  const potion = useRecoveryPotion()
  const qc = useQueryClient()
  const equip = useMutation({
    mutationFn: (code: string | null) =>
      call(api.PATCH('/me/settings', { body: { equipped_title: code } })),
    onSuccess: () => {
      buzz(12)
      void qc.invalidateQueries({ queryKey: keys.status })
    },
  })

  const s = status.data
  if (!s) return <p className="p-6 font-mono text-text-dim">[Loading…]</p>
  const rule = rules.data?.difficulties.find((d) => d.difficulty === s.difficulty)
  const recoveryToday = today.data?.quest.day_kind === 'recovery'
  const error = potion.error ?? equip.error

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <h1 className="font-display text-3xl font-extrabold tracking-tight">Inventory</h1>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="card flex flex-col gap-3 p-5">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-xl bg-mint/15 text-lg text-mint">
              <FontAwesomeIcon icon={faFlask} />
            </span>
            <div>
              <h2 className="text-xs text-text-dim">Recovery Potions</h2>
              <p className="font-display text-2xl font-black">
                <CountUp value={s.recovery_potions} />
                {rule && <span className="text-text-dim"> / {rule.max_potions}</span>}
              </p>
            </div>
          </div>
          <p className="text-sm text-text-dim">
            Earned by clearing a Recovery Day.
            {rule &&
              rules.data &&
              ` Use up to ${rule.max_potions} in any ${rules.data.potion_use_window_days} days.`}
          </p>
          <button
            onClick={() => potion.mutate()}
            disabled={potion.isPending || recoveryToday || s.recovery_potions === 0}
            className="chip"
          >
            Use on today
          </button>
        </section>

        <section className="card flex items-center gap-3 p-5">
          <span className="grid size-11 place-items-center rounded-xl bg-beige/15 text-lg text-beige">
            <FontAwesomeIcon icon={faCoins} />
          </span>
          <div>
            <h2 className="text-xs text-text-dim">Gold</h2>
            <p className="font-display text-2xl font-black">
              <CountUp value={s.gold} />
            </p>
          </div>
        </section>
      </div>

      {error && (
        <p role="alert" className="font-mono text-sm text-danger">
          {error.message}
        </p>
      )}

      <section className="card p-5">
        <h2 className="mb-3 flex items-center gap-2 font-display text-xl font-extrabold">
          <FontAwesomeIcon icon={faCrown} className="text-xp" /> Titles
        </h2>
        {s.titles.length === 0 ? (
          <p className="font-mono text-sm text-text-dim">[No Titles yet. Keep your streak.]</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {s.titles.map((t) => {
              const on = s.title?.code === t.code
              return (
                <li
                  key={t.code}
                  className="flex items-center gap-3 rounded-xl border border-border p-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold">{t.name}</p>
                    <p className="text-xs text-text-dim">{t.description}</p>
                  </div>
                  <button
                    onClick={() => equip.mutate(on ? null : t.code)}
                    disabled={equip.isPending}
                    className={`chip shrink-0 ${on ? 'is-active' : ''}`}
                  >
                    {on ? 'Equipped' : 'Equip'}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </section>
    </div>
  )
}
