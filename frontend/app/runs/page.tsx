'use client'

import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import StatCard from '@/components/ui/StatCard'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'

export default function RunsPage() {
  const { stats, version, error } = useLiveMetrics(3000)

  if (error && !stats) {
    return (
      <div className="flex items-center justify-center h-full text-surface-400">
        <div className="text-center space-y-2">
          <div className="text-3xl text-danger">⚠</div>
          <p className="text-lg font-medium">Unable to load runs</p>
          <p className="text-sm text-surface-500">{error}</p>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner />
      </div>
    )
  }

  const sandboxTotal = (stats.sandbox_passes || 0) + (stats.sandbox_fails || 0)
  const passRate = sandboxTotal > 0 ? ((stats.sandbox_passes / sandboxTotal) * 100).toFixed(0) : '—'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100">Execution History</h2>
        <p className="text-sm text-surface-400 mt-1">Summary of all task executions</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Requests" value={stats.total_requests || 0} />
        <StatCard label="Sandbox Passes" value={stats.sandbox_passes || 0} color="success" />
        <StatCard label="Sandbox Fails" value={stats.sandbox_fails || 0} color="danger" />
        <StatCard label="Pass Rate" value={passRate === '—' ? '—' : `${passRate}%`} color={sandboxTotal > 0 ? (Number(passRate) >= 50 ? 'success' : 'danger') : 'default'} />
      </div>

      <div className="bg-surface-800 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Sandbox Results</h3>
        {sandboxTotal === 0 ? (
          <div className="flex items-center gap-2 text-surface-500 text-sm py-4">
            <span className="text-base">○</span>
            <span>No sandbox executions yet. Submit a task from the dashboard to see results here.</span>
          </div>
        ) : (
          <div className="w-full bg-surface-900 rounded h-6 overflow-hidden flex">
            {stats.sandbox_passes > 0 && (
              <div className="bg-success h-full transition-all duration-1000 flex items-center justify-center text-[10px] font-semibold text-white" style={{ width: `${(stats.sandbox_passes / sandboxTotal) * 100}%` }}>
                {stats.sandbox_passes > 0 ? `${((stats.sandbox_passes / sandboxTotal) * 100).toFixed(0)}%` : ''}
              </div>
            )}
            {stats.sandbox_fails > 0 && (
              <div className="bg-danger h-full transition-all duration-1000 flex items-center justify-center text-[10px] font-semibold text-white" style={{ width: `${(stats.sandbox_fails / sandboxTotal) * 100}%` }}>
                {stats.sandbox_fails > 0 ? `${((stats.sandbox_fails / sandboxTotal) * 100).toFixed(0)}%` : ''}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-surface-800 rounded-lg p-4 space-y-2">
        <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Last Execution</h3>
        {stats.last_generate_duration_ms ? (
          <div className="flex items-center gap-3 text-sm text-surface-400">
            <Badge text={`${(stats.last_generate_duration_ms / 1000).toFixed(1)}s`} />
            <span>Duration</span>
            <span className="text-surface-600">|</span>
            <span>Refreshes automatically</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-surface-500 text-sm py-2">
            <span className="text-base">○</span>
            <span>No executions recorded yet</span>
          </div>
        )}
      </div>

      <div className="bg-surface-800 rounded-lg p-4 space-y-2">
        <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Models</h3>
        {version?.models?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-surface-400 text-xs uppercase tracking-wide">
                  <th className="text-left py-2 pr-4">Role</th>
                  <th className="text-left py-2 pr-4">Model</th>
                  <th className="text-left py-2">Port</th>
                </tr>
              </thead>
              <tbody className="text-surface-300">
                {version.models.map((m) => (
                  <tr key={m.port} className="border-t border-surface-700">
                    <td className="py-2 pr-4"><Badge text={m.role} color="accent" /></td>
                    <td className="py-2 pr-4 font-mono text-xs">{m.name}</td>
                    <td className="py-2">{m.port}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-surface-500 text-sm">Loading model info...</div>
        )}
      </div>
    </div>
  )
}
