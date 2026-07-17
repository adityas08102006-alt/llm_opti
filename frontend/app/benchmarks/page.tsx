'use client'

import { useRef, useEffect, useState } from 'react'
import type { Chart } from 'chart.js'
import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import StatCard from '@/components/ui/StatCard'
import Spinner from '@/components/ui/Spinner'

export default function BenchmarksPage() {
  const { stats, error } = useLiveMetrics(3000)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const chartRef = useRef<Chart | null>(null)
  const [history] = useState<{ ts: number; pp1: number; tg1: number; pp2: number; tg2: number }[]>([])

  useEffect(() => {
    if (!stats?.llama_metrics) return
    const m1 = stats.llama_metrics['8001'] || {}
    const m2 = stats.llama_metrics['8002'] || {}
    const pp1 = m1['llamacpp:prompt_tokens_seconds']
    const tg1 = m1['llamacpp:predicted_tokens_seconds']
    const pp2 = m2['llamacpp:prompt_tokens_seconds']
    const tg2 = m2['llamacpp:predicted_tokens_seconds']
    const entry = { ts: Date.now(), pp1: pp1 ? 1 / pp1 : 0, tg1: tg1 ? 1 / tg1 : 0, pp2: pp2 ? 1 / pp2 : 0, tg2: tg2 ? 1 / tg2 : 0 }
    history.push(entry)
    if (history.length > 30) history.shift()
  }, [stats])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || typeof window === 'undefined') return
    let destroyed = false
    const initChart = async () => {
      const { Chart: ChartClass, registerables } = await import('chart.js')
      ChartClass.register(...registerables)
      if (destroyed) return
      const labels = history.map(() => '')
      const inst = new ChartClass(canvas, {
        type: 'line',
        data: {
          labels,
          datasets: [
            { label: '7B Code gen (t/s)', data: history.map(h => h.tg1), borderColor: '#3b82f6', backgroundColor: '#3b82f620', fill: true, tension: 0.3, pointRadius: 0 },
            { label: '1.5B Docs gen (t/s)', data: history.map(h => h.tg2), borderColor: '#22c55e', backgroundColor: '#22c55e20', fill: true, tension: 0.3, pointRadius: 0 },
            { label: '7B Code prompt (t/s)', data: history.map(h => h.pp1), borderColor: '#f59e0b', backgroundColor: '#f59e0b20', fill: true, tension: 0.3, pointRadius: 0, borderDash: [4, 4] },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 300 },
          scales: {
            y: { beginAtZero: true, ticks: { color: '#94a3b8', maxTicksLimit: 5 } },
            x: { display: false },
          },
          plugins: {
            legend: { labels: { color: '#94a3b8', boxWidth: 12, padding: 8, font: { size: 10 } } },
          },
        },
      })
      if (!destroyed) { chartRef.current = inst }
    }
    initChart()
    return () => { destroyed = true; chartRef.current?.destroy() }
  }, [])

  useEffect(() => {
    const c = chartRef.current
    if (!c) return
    c.data.labels = history.map(() => '')
    c.data.datasets[0].data = history.map(h => h.tg1)
    c.data.datasets[1].data = history.map(h => h.tg2)
    c.data.datasets[2].data = history.map(h => h.pp1)
    c.update('none')
  }, [history])

  if (error && !stats) {
    return (
      <div className="flex items-center justify-center h-full text-surface-400">
        <div className="text-center space-y-2">
          <div className="text-3xl text-danger">⚠</div>
          <p className="text-lg font-medium">Unable to load benchmark data</p>
          <p className="text-sm text-surface-500">{error}</p>
        </div>
      </div>
    )
  }

  const m1 = stats?.llama_metrics?.['8001'] || {}
  const m2 = stats?.llama_metrics?.['8002'] || {}
  const pp1 = m1['llamacpp:prompt_tokens_seconds']
  const tg1 = m1['llamacpp:predicted_tokens_seconds']
  const pp2 = m2['llamacpp:prompt_tokens_seconds']
  const tg2 = m2['llamacpp:predicted_tokens_seconds']

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-surface-100">Benchmarks</h2>
        <p className="text-sm text-surface-400 mt-1">Live throughput and performance metrics</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="7B Code Prompt" value={pp1 ? `${(1 / pp1).toFixed(1)} t/s` : 'idle'} sub="Prompt processing" />
        <StatCard label="7B Code Generate" value={tg1 ? `${(1 / tg1).toFixed(1)} t/s` : 'idle'} sub="Token generation" color={tg1 ? 'success' : 'default'} />
        <StatCard label="1.5B Docs Prompt" value={pp2 ? `${(1 / pp2).toFixed(1)} t/s` : 'idle'} sub="Prompt processing" />
        <StatCard label="1.5B Docs Generate" value={tg2 ? `${(1 / tg2).toFixed(1)} t/s` : 'idle'} sub="Token generation" color={tg2 ? 'success' : 'default'} />
      </div>

      {!stats ? (
        <div className="flex items-center justify-center py-12"><Spinner /></div>
      ) : (
        <>
          <div className="bg-surface-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide mb-3">Throughput Over Time</h3>
            <div className="h-64">
              <canvas ref={canvasRef} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-surface-800 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">CPU Utilization</h3>
              <div className="space-y-1">
                {stats.cpu_percent?.map((p, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="w-6 text-right text-surface-400">{i}</span>
                    <div className="flex-1 bg-surface-900 rounded h-3 overflow-hidden">
                      <div className="h-full bg-accent-500 rounded transition-all duration-1000" style={{ width: `${p}%` }} />
                    </div>
                    <span className="w-8 text-right text-surface-400">{p.toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-surface-800 rounded-lg p-4 space-y-3">
              <h3 className="text-sm font-semibold text-surface-300 uppercase tracking-wide">Arm vs Baseline</h3>
              <div className="space-y-3 text-sm">
                <div className="bg-surface-900 rounded p-3">
                  <div className="text-surface-400 text-xs uppercase tracking-wide mb-1">Arm-Optimized Build</div>
                  <div className="text-surface-100 font-mono text-xs">KleidiAI microkernels active</div>
                  <div className="text-surface-400 text-xs mt-1">I8MM / DotProd matmul acceleration</div>
                </div>
                <div className="text-surface-500 text-xs">
                  Run <code className="bg-surface-900 px-1 rounded">llama-bench -p 512 -n 128 -t 8</code> on both builds to see the delta.
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
