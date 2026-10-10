import { motion } from 'motion/react'
import { useEffect, type ReactNode } from 'react'
import { DIFFICULTY_LABELS } from '../lib/difficulty'
import { buzz } from '../lib/haptics'
import { HoloWindow } from './HoloWindow'
import { useRules, useStatus } from '../lib/queries'

const pct = (f: number) => `${Math.round(f * 100)}%`

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="font-display text-lg font-extrabold text-xp">{title}</h3>
      <div className="flex flex-col gap-1.5 text-sm leading-relaxed text-text/90">{children}</div>
    </section>
  )
}

/** The System's rules, unrolled over the Quest page. Numbers come from GET /rules. */
export function RulesScroll({ onClose }: { onClose: () => void }) {
  const { data: r, error } = useRules()
  const { data: status } = useStatus()

  useEffect(() => {
    buzz(12)
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <motion.div
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="The System's rules"
    >
      <div className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <HoloWindow title="Rules" onClose={onClose}>
          <div className="no-scrollbar max-h-[62dvh] overflow-y-auto">
            <p className="mb-5 text-center font-mono text-sm text-system">
              || The System's rules. ||
            </p>

            {error && <p className="font-mono text-sm text-danger">{error.message}</p>}
            {!r && !error && <p className="font-mono text-sm text-text-dim">[Unrolling…]</p>}
            {r && (
              <div className="flex flex-col gap-5">
                <Section title="Daily Quest">
                  <p>
                    A new Daily Quest arrives every day at your reset hour. Clear its Goals before
                    the next reset.
                  </p>
                  <p>
                    A fully cleared day is worth <b>{r.base_daily_xp} XP</b>, shared between its
                    Goals. Clearing every Goal adds <b>+{pct(r.clear_all_bonus)}</b>. More Goals
                    don't mean more XP.
                  </p>
                  <p>
                    Gold: <b>{r.gold_per_xp}</b> per XP. Stats start at <b>{r.base_stat_value}</b>{' '}
                    and gain +1 for every <b>{r.stat_xp_per_point}</b> stat XP from Goals of that
                    stat.
                  </p>
                </Section>

                <Section title="Difficulty">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-text-dim">
                        <tr>
                          <th className="py-1 pr-2 font-semibold">Mode</th>
                          <th className="pr-2 font-semibold">Fails below</th>
                          <th className="pr-2 font-semibold">XP</th>
                          <th className="pr-2 font-semibold">XP lost on fail</th>
                          <th className="font-semibold">Potions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {r.difficulties.map((d) => (
                          <tr
                            key={d.difficulty}
                            className={`border-t border-border ${status?.difficulty === d.difficulty ? 'font-bold text-xp' : ''}`}
                          >
                            <td className="py-1.5 pr-2 font-bold">
                              {DIFFICULTY_LABELS[d.difficulty]}
                              {status?.difficulty === d.difficulty && ' ◂'}
                            </td>
                            <td className="pr-2">{pct(d.fail_below)}</td>
                            <td className="pr-2">{d.xp_multiplier}×</td>
                            <td className="pr-2">
                              {d.xp_loss_fraction === 0
                                ? 'none'
                                : `${pct(d.xp_loss_fraction)} ${d.can_level_down ? 'of a level (can drop a level)' : 'of level progress'}`}
                            </td>
                            <td>{d.max_potions} max</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {r.difficulties
                    .filter((d) => d.max_strikes)
                    .map((d) => (
                      <p key={d.difficulty}>
                        <b>{DIFFICULTY_LABELS[d.difficulty]}</b>: {d.max_strikes} failed days in{' '}
                        {r.strike_window_days} days seals your Hunter Rank until the Penalty Zone is
                        cleared.
                      </p>
                    ))}
                  <p>Difficulty can be changed once per week.</p>
                </Section>

                <Section title="Penalty Zone">
                  <p>
                    A failed Daily Quest sends you to the Penalty Zone: a Penalty Quest you must
                    clear before the next day ends. Your streak resets.
                  </p>
                </Section>

                <Section title="Recovery">
                  <p>
                    <b>Standard Days</b> (no Routines picked) run your <b>Default Routine</b>. They
                    can't fail and keep your streak; clearing them pays a flat{' '}
                    <b>{r.standard_day_gold} Gold</b>, no XP.
                  </p>
                  <p>
                    <b>Recovery Days</b> in your weekly plan are free: they can't fail, don't break
                    your streak, and their optional Goals give {pct(r.recovery_day_xp_factor)} XP.
                  </p>
                  <p>
                    Clear a Recovery Day's quest to earn a <b>Recovery Potion</b> (carry limit per
                    difficulty; you can use at most that many in any {r.potion_use_window_days}{' '}
                    days). Use it on a Training Day when life gets in the way: the day can't fail,
                    your streak is kept, and you get full XP for what you do. Not usable on Recovery
                    Days or once the day is cleared.
                  </p>
                </Section>

                <Section title="Streak & Titles">
                  <p>Your streak counts days in a row that didn't fail. Recovery Days pause it.</p>
                  <ul className="flex flex-wrap gap-2">
                    {r.streaks.map((s) => (
                      <li
                        key={s.days}
                        className="rounded-lg border border-border bg-panel px-2 py-1 text-xs"
                      >
                        {s.days} days · {s.title} · +{s.gold} Gold
                      </li>
                    ))}
                  </ul>
                </Section>

                <Section title="Levels & Hunter Rank">
                  <p>
                    Early levels take a day; later ones take a week or more. As your Hunter Rank
                    rises, Daily Quest targets grow (shown as % of the A-Rank quest).
                  </p>
                  <table className="w-full text-left text-xs">
                    <thead className="text-text-dim">
                      <tr>
                        <th className="py-1 font-semibold">Tiers</th>
                        <th className="font-semibold">Levels</th>
                        <th className="font-semibold">Clears / level</th>
                        <th className="font-semibold">Targets</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.ranks.map((k) => (
                        <tr
                          key={k.rank}
                          className={`border-t border-border ${status?.hunter_rank === k.rank ? 'font-bold text-xp' : ''}`}
                        >
                          <td className="py-1.5 font-display font-black">{k.rank}</td>
                          <td>
                            {k.min_level}
                            {k.max_level ? `–${k.max_level}` : '+'}
                          </td>
                          <td>
                            {k.clears_per_level} ({k.xp_per_level} XP)
                          </td>
                          <td>{pct(k.intensity)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Section>
              </div>
            )}
          </div>
        </HoloWindow>
      </div>
    </motion.div>
  )
}
