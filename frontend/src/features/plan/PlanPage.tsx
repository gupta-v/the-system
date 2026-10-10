import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowLeft } from '@fortawesome/free-solid-svg-icons'
import { Link } from 'react-router'
import { WeeklyPlan } from '../profile/WeeklyPlan'
import { GoalEditor } from './GoalEditor'

/** Customize your plan: the week, the Goals and the Routines. */
export function PlanPage() {
  return (
    <div className="mx-auto flex max-w-xl flex-col gap-5">
      <header className="flex items-center gap-3">
        <Link to="/profile" aria-label="Back to Profile" className="chip press size-11 px-0">
          <FontAwesomeIcon icon={faArrowLeft} />
        </Link>
        <h1 className="font-display text-4xl font-extrabold tracking-tight">Your plan</h1>
      </header>
      <WeeklyPlan goalSection={<GoalEditor />} />
    </div>
  )
}
