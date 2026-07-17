'use client'

import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import StatCard from '@/components/ui/StatCard'
import Badge from '@/components/ui/Badge'
import KleidiaiBadge from '@/components/Dashboard/KleidiaiBadge'
import Spinner from '@/components/ui/Spinner'

export default function ModelsPage() {
  const { version, arm, error } = useLiveMetrics(5000)

  if (error && !version) {
    return (
      <div className="flex items-center justify-center h-full text-surface-400">
        <div className="text-center space-y-2">
          <div className="text-3xl text-danger">⚠</div>
          <p className="text-lg font-medium">Unable to load model info</p>
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
        <h2 className="text-lg font-semibold text-surface-100">Models</h2>
        <p className="text-sm text-surface-400 mt-1">Inference models and quantization</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Code Model" value={version.models?.[0]?.name?.split('-q')[0] || '—'} sub={`Port ${version.models?.[0]?.port || '—'}`} />
        <StatCard label="Docs Model" value={version.models?.[1]?.name?.split('-q')[0] || '—'} sub={`Port ${version.models?.[1]?.port || '—'}`} />
        <StatCard label="Quantization" value="Q4_K_M" sub="Default runtime" />
        <StatCard label="KleidiAI" value={<KleidiaiBadge arm={arm} />} />
      </div>

      <div className="bg-surface-800 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Deployed Models</h3>
        {version.models?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-surface-400 text-xs uppercase tracking-wide">
                  <th className="text-left py-2 pr-4">Role</th>
                  <th className="text-left py-2 pr-4">Model</th>
                  <th className="text-left py-2 pr-4">Port</th>
                  <th className="text-left py-2">Format</th>
                </tr>
              </thead>
              <tbody className="text-surface-300">
                {version.models.map((m) => (
                  <tr key={m.port} className="border-t border-surface-700">
                    <td className="py-2 pr-4"><Badge text={m.role} color="accent" /></td>
                    <td className="py-2 pr-4 font-mono text-xs">{m.name}</td>
                    <td className="py-2 pr-4">{m.port}</td>
                    <td className="py-2"><Badge text="GGUF" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-surface-500 text-sm">No model data available</div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-surface-800 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Quantization Levels</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center py-1 border-b border-surface-700">
              <span className="text-surface-300">Q4_K_M</span>
              <span className="text-surface-400">~4.7 GB — Default (balanced)</span>
            </div>
            <div className="flex justify-between items-center py-1 border-b border-surface-700">
              <span className="text-surface-300">Q5_K_M</span>
              <span className="text-surface-400">~5.4 GB — Higher quality</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-surface-300">Q8_0</span>
              <span className="text-surface-400">~8 GB — Maximum quality</span>
            </div>
          </div>
        </div>

        <div className="bg-surface-800 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Arm Optimization</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-surface-300">KleidiAI</span>
              <Badge text={arm?.kleidiai_build ? 'ON' : 'OFF'} color={arm?.kleidiai_build ? 'success' : 'danger'} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-surface-300">Arm Arch Target</span>
              <span className="text-surface-400 font-mono text-xs">{arm?.arm_arch || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-surface-300">NEON</span>
              <Badge text={arm?.neon ? '✓' : '—'} color={arm?.neon ? 'success' : 'neutral'} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-surface-300">DotProd</span>
              <Badge text={arm?.dotprod ? '✓' : '—'} color={arm?.dotprod ? 'success' : 'neutral'} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-surface-300">I8MM</span>
              <Badge text={arm?.i8mm ? '✓' : '—'} color={arm?.i8mm ? 'success' : 'neutral'} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-surface-300">SVE</span>
              <Badge text={arm?.sve ? '✓' : '—'} color={arm?.sve ? 'success' : 'neutral'} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
