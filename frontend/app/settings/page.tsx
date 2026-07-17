'use client'

import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import StatCard from '@/components/ui/StatCard'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'

export default function SettingsPage() {
  const { version, arm, stats, error } = useLiveMetrics(10000)

  if (error && !version) {
    return (
      <div className="flex items-center justify-center h-full text-surface-400">
        <div className="text-center space-y-2">
          <div className="text-3xl text-danger">⚠</div>
          <p className="text-lg font-medium">Unable to load configuration</p>
          <p className="text-sm text-surface-500">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100">Settings</h2>
        <p className="text-sm text-surface-400 mt-1">System configuration and environment</p>
      </div>

      {!version ? (
        <div className="flex items-center justify-center py-12"><Spinner /></div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="API Version" value={version.version || '—'} />
            <StatCard label="Runtime" value={`Python ${version.python_version || '—'}`} />
            <StatCard label="Uptime" value={version ? `${Math.floor(version.uptime_seconds / 60)}m` : '—'} />
            <StatCard label="Models Deployed" value={version.models?.length || 0} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-surface-800 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">API Configuration</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
                  <span className="text-surface-300">Base URL</span>
                  <span className="text-surface-400 font-mono text-xs">{process.env.NEXT_PUBLIC_API_URL || '/api'}</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
                  <span className="text-surface-300">API Key</span>
                  <span className="text-surface-400 font-mono text-xs">{process.env.NEXT_PUBLIC_API_KEY ? '••••••••' : 'Not set'}</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
                  <span className="text-surface-300">Backend Host</span>
                  <span className="text-surface-400 font-mono text-xs">3.107.210.17:9000</span>
                </div>
                <div className="flex justify-between items-center py-1.5">
                  <span className="text-surface-300">Framework</span>
                  <Badge text="Next.js 15" color="accent" />
                </div>
              </div>
            </div>

            <div className="bg-surface-800 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Model Configuration</h3>
              <div className="space-y-3 text-sm">
                {version.models?.map((m) => (
                  <div key={m.port} className="bg-surface-900 rounded p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-surface-200 font-medium capitalize">{m.role}</span>
                      <Badge text={`Port ${m.port}`} />
                    </div>
                    <div className="text-xs text-surface-400 font-mono break-all">{m.name}</div>
                  </div>
                ))}
                {!version.models?.length && <div className="text-surface-500 text-sm">No models configured</div>}
              </div>
            </div>
          </div>

          <div className="bg-surface-800 rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Optimization Flags</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div className="bg-surface-900 rounded p-3 text-center">
                <div className="text-surface-400 text-xs uppercase tracking-wide mb-1">KleidiAI</div>
                <Badge text={arm?.kleidiai_build ? 'ON' : 'OFF'} color={arm?.kleidiai_build ? 'success' : 'danger'} />
              </div>
              <div className="bg-surface-900 rounded p-3 text-center">
                <div className="text-surface-400 text-xs uppercase tracking-wide mb-1">GGML_NATIVE</div>
                <Badge text="OFF" color="warning" />
              </div>
              <div className="bg-surface-900 rounded p-3 text-center">
                <div className="text-surface-400 text-xs uppercase tracking-wide mb-1">Arm Arch</div>
                <span className="text-surface-300 font-mono text-xs">{arm?.arm_arch || 'generic'}</span>
              </div>
              <div className="bg-surface-900 rounded p-3 text-center">
                <div className="text-surface-400 text-xs uppercase tracking-wide mb-1">Quant</div>
                <span className="text-surface-300 font-mono text-xs">Q4_K_M</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
