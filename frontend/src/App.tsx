import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faBoxOpen,
  faCalendarDays,
  faChartSimple,
  faRightFromBracket,
  faListCheck,
  faScroll,
  faUser,
} from '@fortawesome/free-solid-svg-icons'
import { useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'motion/react'
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useOutlet,
} from 'react-router'
import { HeroArt } from './components/HeroArt'
import { PlanPage } from './features/plan/PlanPage'
import { ProfilePage } from './features/profile/ProfilePage'
import { AuthPage } from './features/auth/AuthPage'
import { HistoryPage } from './features/history/HistoryPage'
import { InventoryPage } from './features/inventory/InventoryPage'
import { AwakeningPage } from './features/onboarding/AwakeningPage'
import { HomePage } from './features/quests/HomePage'
import { StatusPage } from './features/status/StatusPage'
import { ApiError, api } from './lib/api'
import { useToday } from './lib/queries'

const NAV = [
  { to: '/', label: 'Quest', icon: faListCheck },
  { to: '/inventory', label: 'Inventory', icon: faBoxOpen },
  { to: '/status', label: 'Rating', icon: faChartSimple },
  { to: '/history', label: 'History', icon: faCalendarDays },
  { to: '/profile', label: 'Profile', icon: faUser },
]

/** Routes by what the backend says: 401 → login, 409 → not Awakened yet. */
function Guard() {
  const today = useToday()
  const err = today.error
  if (err instanceof ApiError && err.status === 401) return <Navigate to="/login" replace />
  if (err instanceof ApiError && err.status === 409) return <Navigate to="/awakening" replace />
  if (err) return <p className="p-6 font-mono text-danger">{err.message}</p>
  return <Layout />
}

function Layout() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const outlet = useOutlet()
  const logout = async () => {
    await api.POST('/auth/logout')
    qc.clear()
    navigate('/login', { replace: true })
  }
  const topLink = ({ isActive }: { isActive: boolean }) =>
    `flex min-h-11 items-center gap-2 rounded-xl px-4 text-sm transition ${
      isActive ? 'bg-text font-semibold text-bg' : 'text-text-dim hover:text-text'
    }`
  // Rules isn't a page: it unrolls a scroll over the Quest page.
  const openRules = () => navigate('/?rules=1')
  const bottomLink = ({ isActive }: { isActive: boolean }) =>
    `flex min-h-14 flex-1 flex-col items-center justify-center gap-1 text-xs ${
      isActive ? 'font-semibold text-xp' : 'text-text-dim'
    }`

  return (
    <div className="mana min-h-dvh pb-20 sm:pb-0">
      <header className="sticky top-0 z-40 bg-bg/60 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-4 py-3">
          <p className="font-display text-xl font-black tracking-tight">
            The System<span className="text-xp">.</span>
          </p>
          <nav className="hidden gap-1 sm:flex">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end className={topLink}>
                <FontAwesomeIcon icon={n.icon} />
                {n.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center">
            {/* Rules opens a scroll over the Quest page, so it sits by Log out rather than in the nav. */}
            <button
              onClick={openRules}
              aria-label="Rules"
              className="grid size-11 place-items-center text-text-dim hover:text-text"
            >
              <FontAwesomeIcon icon={faScroll} />
            </button>
            <button
              onClick={logout}
              aria-label="Log out"
              className="grid size-11 place-items-center text-text-dim hover:text-text"
            >
              <FontAwesomeIcon icon={faRightFromBracket} />
            </button>
          </div>
        </div>
        <div className="system-line" />
      </header>

      <main className="mx-auto max-w-[1200px] px-4 py-5">
        {/* Page transitions: fade + 8px slide, 200 ms (style guide §5). */}
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {outlet}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-bg-elev/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md sm:hidden">
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end className={bottomLink}>
            <FontAwesomeIcon icon={n.icon} className="text-lg" />
            {n.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

export function App() {
  return (
    <BrowserRouter>
      <HeroArt />
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route path="/awakening" element={<AwakeningPage />} />
        <Route element={<Guard />}>
          <Route index element={<HomePage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/plan" element={<PlanPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
