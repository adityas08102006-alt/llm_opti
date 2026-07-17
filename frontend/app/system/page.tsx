'use client'

import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import StatCard from '@/components/ui/StatCard'
import Badge from '@/components/ui/Badge'
import KleidiaiBadge from '@/components/Dashboard/KleidiaiBadge'
import Spinner from '@/components/ui/Spinner'

export default function SystemPage() {
  const { version, arm, stats, error } = useLiveMetrics(5000)

  if (error && !version) {
    return (
      <div className="flex items-center justify-center h-full text-surface-400">
        <div className="text-center space-y-2">
          <div className="text-3xl text-danger">⚠</div>
          <p className="text-lg font-medium">Unable to load system info</p>
          <p className="text-sm text-surface-500">{error}</p>
        </div>
      </div>
    )
  }

  if (!version) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100">System</h2>
        <p className="text-sm text-surface-400 mt-1">Platform and build information</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="API Version" value={version.version || '—'} />
        <StatCard label="Python" value={version.python_version || '—'} />
        <StatCard label="Uptime" value={`${Math.floor(version.uptime_seconds / 60)}m`} sub={`${version.uptime_seconds % 60}s`} />
        <StatCard label="KleidiAI" value={<KleidiaiBadge arm={arm} />} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-surface-800 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Arm CPU Features</h3>
          {arm ? (
            <div className="space-y-2 text-sm">
              {[
                { label: 'NEON (SIMD)', key: 'neon', desc: 'Advanced SIMD for media/audio' },
                { label: 'DotProd (ASIMDDP)', key: 'dotprod', desc: 'Dot-product integer instructions' },
                { label: 'I8MM', key: 'i8mm', desc: 'Int8 matrix multiplication' },
                { label: 'SVE', key: 'sve', desc: 'Scalable Vector Extension' },
              ].map((f) => (
                <div key={f.key} className="flex items-center justify-between py-1.5 border-b border-surface-700 last:border-0">
                  <div>
                    <div className="text-surface-200">{f.label}</div>
                    <div className="text-[10px] text-surface-500">{f.desc}</div>
                  </div>
                  <Badge text={(arm as any)[f.key] ? '✓' : '—'} color={(arm as any)[f.key] ? 'success' : 'neutral'} />
                </div>
              ))}
              <div className="flex items-center justify-between py-1.5 border-b border-surface-700 last:border-0 mt-2 pt-2 border-t border-surface-700">
                <div>
                  <div className="text-surface-200">Arm Arch Target</div>
                  <div className="text-[10px] text-surface-500">Build-time architecture flag</div>
                </div>
                <span className="text-xs font-mono text-accent-400">{arm.arm_arch || 'generic'}</span>
              </div>
            </div>
          ) : (
            <div className="text-surface-500 text-sm">Loading CPU features...</div>
          )}
        </div>

        <div className="bg-surface-800 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Build Info</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
              <span className="text-surface-300">Framework</span>
              <span className="text-surface-400">llama.cpp</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
              <span className="text-surface-300">KleidiAI</span>
              <Badge text={arm?.kleidiai_build ? 'BUILT IN' : 'NOT PRESENT'} color={arm?.kleidiai_build ? 'success' : 'danger'} />
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
              <span className="text-surface-300">Instance Type</span>
              <span className="text-surface-400">Graviton3/4 (Arm64)</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-surface-700">
              <span className="text-surface-300">Backend</span>
              <span className="text-surface-400">FastAPI + Uvicorn</span>
            </div>
            <div className="flex justify-between items-center py-1.5">
              <span className="text-surface-300">GGUF Format</span>
              <Badge text="Q4_K_M" color="accent" />
            </div>
          </div>
        </div>
      </div>

      <div className="bg-surface-800 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Model Deployment</h3>
        {version.models?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-surface-400 text-xs uppercase tracking-wide">
                  <th className="text-left py-2 pr-4">Role</th>
                  <th className="text-left py-2 pr-4">Model</th>
                  <th className="text-left py-2 pr-4">Port</th>
                  <th className="text-left py-2">Quant</th>
                </tr>
              </thead>
              <tbody className="text-surface-300">
                {version.models.map((m) => (
                  <tr key={m.port} className="border-t border-surface-700">
                    <td className="py-2 pr-4"><Badge text={m.role} color="accent" /></td>
                    <td className="py-2 pr-4 font-mono text-xs">{m.name}</td>
                    <td className="py-2 pr-4">{m.port}</td>
                    <td className="py-2">Q4_K_M</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-surface-500 text-sm">No model deployment data</div>
        )}
      </div>
    </div>
  )
}
