'use client'

import { useState, useEffect } from 'react'
import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import { api } from '@/lib/api'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'

interface HealthState {
  api: { status: string } | null
  stats: boolean
  arm: boolean
  error: string | null
}

export default function HealthPage() {
  const { version, error: liveError } = useLiveMetrics(10000)
  const [health, setHealth] = useState<HealthState>({ api: null, stats: false, arm: false, error: null })

  useEffect(() => {
    const check = async () => {
      try {
        const [h, s, a] = await Promise.all([
          api.health().catch(() => null),
          api.stats().then(() => true).catch(() => false),
          api.armVerify().then(() => true).catch(() => false),
        ])
        setHealth({ api: h, stats: s, arm: a, error: null })
      } catch (e) {
        setHealth(p => ({ ...p, error: (e as Error).message }))
      }
    }
    check()
    const id = setInterval(check, 15000)
    return () => clearInterval(id)
  }, [])

  const checks = [
    { name: 'API Server', path: '/health', status: health.api?.status === 'ok' ? 'pass' : health.api === null ? 'pending' : 'fail', detail: health.api ? `Status: ${health.api.status}` : health.error || 'Pending...' },
    { name: 'Metrics Endpoint', path: '/stats', status: health.stats ? 'pass' : health.stats === false && health.api !== null ? 'fail' : 'pending', detail: health.stats ? 'Responding' : health.error || 'Pending...' },
    { name: 'Arm Verification', path: '/system/arm-verify', status: health.arm ? 'pass' : health.arm === false && health.api !== null ? 'fail' : 'pending', detail: health.arm ? 'CPU features verified' : health.error || 'Pending...' },
    { name: 'Code Model (8001)', path: 'llama-server :8001', status: version?.models?.some(m => m.port === 8001) ? 'pass' : version ? 'warn' : 'pending', detail: version?.models?.find(m => m.port === 8001)?.name || 'Unknown' },
    { name: 'Docs Model (8002)', path: 'llama-server :8002', status: version?.models?.some(m => m.port === 8002) ? 'pass' : version ? 'warn' : 'pending', detail: version?.models?.find(m => m.port === 8002)?.name || 'Unknown' },
    { name: 'KleidiAI Build', path: 'Build flag', status: version?.kleidiai?.enabled ? 'pass' : version ? 'fail' : 'pending', detail: version?.kleidiai?.enabled ? `Enabled (${version.kleidiai.arm_arch || 'arm64'})` : 'Not detected' },
  ]

  const statusColor = (s: string) => s === 'pass' ? 'success' : s === 'fail' ? 'danger' : 'warning'
  const statusText = (s: string) => s === 'pass' ? 'OK' : s === 'fail' ? 'FAIL' : '...'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100">Health</h2>
        <p className="text-sm text-surface-400 mt-1">System health checks and service status</p>
      </div>

      <div className="bg-surface-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-surface-700 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Service Status</h3>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-surface-400">Overall:</span>
            <Badge text={checks.every(c => c.status === 'pass') ? 'ALL HEALTHY' : checks.some(c => c.status === 'fail') ? 'ISSUES DETECTED' : 'CHECKING'} color={checks.every(c => c.status === 'pass') ? 'success' : checks.some(c => c.status === 'fail') ? 'danger' : 'warning'} />
          </div>
        </div>
        <div className="divide-y divide-surface-700">
          {checks.map((c) => (
            <div key={c.name} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${c.status === 'pass' ? 'bg-success' : c.status === 'fail' ? 'bg-danger' : 'bg-warning animate-pulse'}`} />
                <div>
                  <div className="text-sm text-surface-200 font-medium">{c.name}</div>
                  <div className="text-xs text-surface-500 font-mono">{c.path}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-surface-400 max-w-48 text-right truncate">{c.detail}</span>
                <Badge text={statusText(c.status)} color={statusColor(c.status) as any} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-surface-800 rounded-lg p-4 space-y-2">
        <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Connection</h3>
        <div className="flex items-center gap-2 text-sm text-surface-400">
          <Badge text={liveError ? 'disconnected' : 'connected'} color={liveError ? 'danger' : 'success'} />
          <span>{liveError ? liveError : 'Live metrics stream active'}</span>
        </div>
        {version && (
          <div className="text-xs text-surface-500 mt-1">
            Uptime: {Math.floor(version.uptime_seconds / 60)}m {version.uptime_seconds % 60}s &middot; Python {version.python_version}
          </div>
        )}
      </div>
    </div>
  )
}
