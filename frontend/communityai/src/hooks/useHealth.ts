import { useEffect, useState } from 'react'

import { getHealthStatus } from '../services/health'
import type { HealthStatus } from '../types/health'

type HealthState =
  | { status: 'loading'; data: null; error: null }
  | { status: 'ready'; data: HealthStatus; error: null }
  | { status: 'error'; data: null; error: string }

const initialState: HealthState = {
  status: 'loading',
  data: null,
  error: null,
}

export function useHealth() {
  const [state, setState] = useState<HealthState>(initialState)

  useEffect(() => {
    let active = true

    getHealthStatus()
      .then((data) => {
        if (active) {
          setState({ status: 'ready', data, error: null })
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: 'error',
            data: null,
            error:
              error instanceof Error
                ? error.message
                : 'Unable to reach the backend',
          })
        }
      })

    return () => {
      active = false
    }
  }, [])

  return state
}
