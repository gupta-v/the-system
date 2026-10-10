import { createContext, useContext } from 'react'
import type { Notice } from './api'

export const PushNotices = createContext<(notices: Notice[]) => void>(() => {})

export const usePushNotices = () => useContext(PushNotices)
