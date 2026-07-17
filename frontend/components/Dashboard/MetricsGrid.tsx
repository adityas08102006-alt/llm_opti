'use client'

import StatCard from '@/components/ui/StatCard'
import type { StatsResponse } from '@/lib/api'

interface MetricsGridProps {
  stats: StatsResponse | null
  totalRequests: number
  sandboxPasses: number
  lastDuration: number
}

export default function MetricsGrid({ stats, totalRequests, sandboxPasses, lastDuration }: MetricsGridProps) {
  const port8001 = stats?.llama_metrics?.['8001'] || {}
  const port8002 = stats?.llama_metrics?.['8002'] || {}

  const pp1 = port8001['llamacpp:prompt_tokens_seconds']
  const tg1 = port8001['llamacpp:predicted_tokens_seconds']
  const pp2 = port8002['llamacpp:prompt_tokens_seconds']
  const tg2 = port8002['llamacpp:predicted_tokens_seconds']

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard label="Total Requests" value={totalRequests} />
      <StatCard label="Last Duration" value={lastDuration ? `${(lastDuration / 1000).toFixed(1)}s` : '—'} />
      <StatCard label="Sandbox Passed" value={sandboxPasses} color="success" />
      <div className="bg-surface-800 rounded-lg p-4 text-center col-span-2 md:col-span-1">
        <div className="text-xs text-surface-400 uppercase tracking-wide">CPU Cores</div>
        <div className="mt-2 space-y-1">
          {stats?.cpu_percent?.map((p, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="w-6 text-right text-surface-400">{i}</span>
              <div className="flex-1 bg-surface-900 rounded h-2 overflow-hidden">
                <div className="h-full bg-accent-500 rounded transition-all duration-1000" style={{ width: `${p}%` }} />
              </div>
              <span className="w-8 text-right text-surface-400">{p.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-surface-800 rounded-lg p-4 col-span-2 md:col-span-2">
        <div className="text-xs text-surface-400 uppercase tracking-wide mb-2">Model Throughput</div>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div>
            <div className="text-[10px] text-surface-400">Port 8001 (7B Code)</div>
            <div className="text-sm font-semibold text-surface-100">
              {pp1 ? `${(1 / pp1).toFixed(1)} t/s` : 'idle'}
            </div>
            <div className="text-[10px] text-surface-400">gen: {tg1 ? `${(1 / tg1).toFixed(1)} t/s` : '—'}</div>
          </div>
          <div>
            <div className="text-[10px] text-surface-400">Port 8002 (1.5B Docs)</div>
            <div className="text-sm font-semibold text-surface-100">
              {pp2 ? `${(1 / pp2).toFixed(1)} t/s` : 'idle'}
            </div>
            <div className="text-[10px] text-surface-400">gen: {tg2 ? `${(1 / tg2).toFixed(1)} t/s` : '—'}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
