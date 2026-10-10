import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { SystemWindow } from '../../components/SystemWindow'
import { api, call } from '../../lib/api'

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const qc = useQueryClient()

  const submit = useMutation({
    mutationFn: () =>
      call(
        mode === 'login'
          ? api.POST('/auth/login', { body: { email, password } })
          : api.POST('/auth/register', { body: { email, password } }),
      ),
    onSuccess: (session) => {
      qc.clear()
      navigate(session.awakened ? '/' : '/awakening', { replace: true })
    },
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    submit.mutate()
  }

  return (
    <main className="grid min-h-dvh place-items-center p-4">
      <SystemWindow title={mode === 'login' ? 'Player login' : 'New player'} className="w-full max-w-sm">
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm text-text-dim">
            Email
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="min-h-11 rounded-xl border border-border bg-bg px-3 text-text outline-none focus:border-accent"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-text-dim">
            Password
            <input
              type="password"
              required
              minLength={8}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="min-h-11 rounded-xl border border-border bg-bg px-3 text-text outline-none focus:border-accent"
            />
          </label>
          {submit.error && (
            <p role="alert" className="font-mono text-sm text-danger">
              {submit.error.message}
            </p>
          )}
          <button
            disabled={submit.isPending}
            className="btn"
          >
            {mode === 'login' ? 'Enter' : 'Register'}
          </button>
          <button
            type="button"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="min-h-11 text-sm text-text-dim hover:text-text"
          >
            {mode === 'login' ? 'No account? Register' : 'Have an account? Log in'}
          </button>
        </form>
      </SystemWindow>
    </main>
  )
}
