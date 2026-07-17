'use client'

import { useState, useEffect, useRef } from 'react'
import { api, type StatsResponse, type ArmVerifyResponse, type VersionResponse } from '@/lib/api'

export interface LiveData {
  stats: StatsResponse | null
  arm: ArmVerifyResponse | null
  version: VersionResponse | null
  demoMode: string | null
  error: string | null
}

export function useLiveMetrics(interval = 3000) {
  const [data, setData] = useState<LiveData>({
    stats: null, arm: null, version: null, demoMode: null, error: null,
  })
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true
    const fetchAll = async () => {
      try {
        const [stats, arm, version, dm] = await Promise.all([
          api.stats(),
          api.armVerify(),
          api.version(),
          api.demoMode(),
        ])
        if (mounted.current) setData({ stats, arm, version, demoMode: dm.demo_mode, error: null })
      } catch (e) {
        if (mounted.current) setData((p) => ({ ...p, error: (e as Error).message }))
      }
    }
    fetchAll()
    const id = setInterval(fetchAll, interval)
    return () => { mounted.current = false; clearInterval(id) }
  }, [interval])

  return data
}
