'use client'

import { useRef, useEffect, useState } from 'react'
import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import StatCard from '@/components/ui/StatCard'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'

export default function MetricsPage() {
  const { stats, version, error } = useLiveMetrics(2000)
  const cpuCanvasRef = useRef<HTMLCanvasElement>(null)
  const [cpuHistory] = useState<number[][]>([])
  const [cpuChart, setCpuChart] = useState<any>(null)

  useEffect(() => {
    if (!stats?.cpu_percent) return
    cpuHistory.push([...stats.cpu_percent])
    if (cpuHistory.length > 60) cpuHistory.shift()
  }, [stats])

  useEffect(() => {
    if (!cpuCanvasRef.current || typeof window === 'undefined') return
    let destroyed = false
    const init = async () => {
      const { Chart: C, registerables } = await import('chart.js')
      C.register(...registerables)
      if (destroyed) return
      const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#ec4899', '#14b8a6', '#f97316']
      const datasets = Array.from({ length: 8 }, (_, i) => ({
        label: `Core ${i}`,
        data: [] as number[],
        borderColor: colors[i % colors.length],
        backgroundColor: `${colors[i % colors.length]}20`,
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1,
      }))
      const inst = new C(cpuCanvasRef.current, {
        type: 'line',
        data: { labels: [], datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 200 },
          scales: {
            y: { min: 0, max: 100, ticks: { color: '#94a3b8', maxTicksLimit: 5, callback: (v: any) => `${v}%` } },
            x: { display: false },
          },
          plugins: {
            legend: { labels: { color: '#94a3b8', boxWidth: 12, padding: 8, font: { size: 10 } } },
          },
        },
      })
      if (!destroyed) setCpuChart(inst)
    }
    init()
    return () => { destroyed = true; cpuChart?.destroy() }
  }, [])

  useEffect(() => {
    if (!cpuChart || cpuHistory.length === 0) return
    const labels = cpuHistory.map(() => '')
    cpuChart.data.labels = labels
    for (let i = 0; i < 8; i++) {
      cpuChart.data.datasets[i].data = cpuHistory.map(h => h[i] ?? 0)
    }
    cpuChart.update('none')
  }, [cpuHistory])

  if (error && !stats) {
    return (
      <div className="flex items-center justify-center h-full text-surface-400">
        <div className="text-center space-y-2">
          <div className="text-3xl text-danger">⚠</div>
          <p className="text-lg font-medium">Unable to load metrics</p>
          <p className="text-sm text-surface-500">{error}</p>
        </div>
      </div>
    )
  }

  const m1 = stats?.llama_metrics?.['8001'] || {}
  const m2 = stats?.llama_metrics?.['8002'] || {}
  const tg1 = m1['llamacpp:predicted_tokens_seconds']
  const tg2 = m2['llamacpp:predicted_tokens_seconds']

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100">Live Metrics</h2>
        <p className="text-sm text-surface-400 mt-1">Real-time system performance data</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Uptime" value={version ? `${Math.floor(version.uptime_seconds / 60)}m ${version.uptime_seconds % 60}s` : '—'} />
        <StatCard label="Total Requests" value={stats?.total_requests || 0} />
        <StatCard label="Python" value={version?.python_version || '—'} sub="Runtime version" />
        <StatCard label="API Version" value={version?.version || '—'} />
      </div>

      {!stats ? (
        <div className="flex items-center justify-center py-12"><Spinner /></div>
      ) : (
        <>
          <div className="bg-surface-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide mb-3">CPU Usage Per Core (last 60 samples)</h3>
            <div className="h-72">
              <canvas ref={cpuCanvasRef} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-surface-800 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Current CPU</h3>
              {stats.cpu_percent?.map((p, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="w-6 text-right text-surface-400">C{i}</span>
                  <div className="flex-1 bg-surface-900 rounded h-4 overflow-hidden">
                    <div className="h-full bg-accent-500 rounded transition-all duration-700" style={{ width: `${p}%` }} />
                  </div>
                  <span className="w-8 text-right text-surface-400">{p.toFixed(0)}%</span>
                  <div className="w-16 h-4 flex items-center justify-center rounded text-[10px] font-medium" style={{ background: p > 80 ? '#ef444420' : p > 50 ? '#f59e0b20' : '#22c55e20', color: p > 80 ? '#ef4444' : p > 50 ? '#f59e0b' : '#22c55e' }}>
                    {p > 80 ? 'HIGH' : p > 50 ? 'MED' : 'LOW'}
                  </div>
                </div>
              ))}
              {!stats.cpu_percent?.length && <div className="text-surface-500 text-sm">No CPU data</div>}
            </div>

            <div className="bg-surface-800 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Model Throughput</h3>
              <div className="space-y-3">
                <div className="bg-surface-900 rounded p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-surface-300 font-medium">Port 8001 — 7B Code</span>
                    <Badge text={tg1 ? 'active' : 'idle'} color={tg1 ? 'success' : 'neutral'} />
                  </div>
                  <div className="text-lg font-bold text-accent-400">{tg1 ? `${(1 / tg1).toFixed(1)}` : '—'}<span className="text-xs text-surface-400 font-normal"> t/s</span></div>
                  <div className="text-[10px] text-surface-500">Generation throughput</div>
                </div>
                <div className="bg-surface-900 rounded p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-surface-300 font-medium">Port 8002 — 1.5B Docs</span>
                    <Badge text={tg2 ? 'active' : 'idle'} color={tg2 ? 'success' : 'neutral'} />
                  </div>
                  <div className="text-lg font-bold text-success">{tg2 ? `${(1 / tg2).toFixed(1)}` : '—'}<span className="text-xs text-surface-400 font-normal"> t/s</span></div>
                  <div className="text-[10px] text-surface-500">Generation throughput</div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
