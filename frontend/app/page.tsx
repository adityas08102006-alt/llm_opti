'use client'

import { useState } from 'react'
import { useLiveMetrics } from '@/hooks/useLiveMetrics'
import { api, type GenerateResponse } from '@/lib/api'
import MetricsGrid from '@/components/Dashboard/MetricsGrid'
import KleidiaiBadge from '@/components/Dashboard/KleidiaiBadge'
import StatCard from '@/components/ui/StatCard'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'

export default function DashboardPage() {
  const { stats, arm, version } = useLiveMetrics(3000)
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await api.generate(prompt)
      setResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top info bar */}
      <div className="flex items-center gap-4 flex-wrap">
        <StatCard label="Backend" value={version?.version || '—'} sub={version?.python_version || ''} />
        <StatCard label="KleidiAI" value={<KleidiaiBadge arm={arm} />} />
        <StatCard label="Uptime" value={version ? `${Math.floor(version.uptime_seconds / 60)}m` : '—'} />
        <StatCard
          label="Models"
          value={version?.models?.length || 0}
          sub={version?.models?.map((m) => m.role).join(', ') || ''}
        />
      </div>

      {/* Live metrics */}
      <MetricsGrid
        stats={stats}
        totalRequests={stats?.total_requests ?? 0}
        sandboxPasses={stats?.sandbox_passes ?? 0}
        lastDuration={stats?.last_generate_duration_ms ?? 0}
      />

      {/* Prompt input */}
      <div className="bg-surface-800 rounded-lg p-4 space-y-3">
        <textarea
          className="w-full bg-surface-900 border border-surface-700 rounded p-3 text-sm text-surface-200 placeholder-surface-600 resize-none focus:outline-none focus:border-accent-500"
          rows={3}
          placeholder="Describe the task…&#10;&#10;Example: Write a Python function for fibonacci with unit tests"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={loading || !prompt.trim()}
            className="bg-accent-500 hover:bg-accent-600 disabled:bg-surface-700 disabled:text-surface-500 text-white px-5 py-2 rounded text-sm font-medium transition-colors"
          >
            {loading ? 'Executing…' : 'Execute'}
          </button>
          {loading && <Spinner />}
          {error && <span className="text-danger text-sm">{error}</span>}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <StatCard label="DAG Shape" value={result.dag_shape} />
            <StatCard label="Duration" value={`${(result.total_duration_ms / 1000).toFixed(1)}s`} />
            <StatCard label="Subtasks" value={result.subtasks.length} />
            <StatCard
              label="Sandbox"
              value={result.sandbox?.passed ? 'PASS' : 'FAIL'}
              color={result.sandbox?.passed ? 'success' : 'danger'}
            />
            <StatCard label="Regenerations" value={result.regeneration_attempts} />
            <StatCard label="Verified" value={result.fully_verified ? 'YES' : 'NO'} color={result.fully_verified ? 'success' : 'warning'} />
          </div>
          {result.cached && (
            <div className="flex items-center gap-2 text-warning text-sm">
              <Badge text="Cached" color="warning" />
              <span>Result served from golden-path cache</span>
            </div>
          )}

          {/* Subtask details */}
          {result.subtasks.map((s) => (
            <div key={s.subtask_id} className="bg-surface-800 rounded-lg p-4 border-l-2 border-accent-500 space-y-2">
              <div className="flex items-center gap-3 text-sm">
                <span className="font-semibold text-accent-400">{s.name}</span>
                <Badge text={`${(s.total_duration_ms / 1000).toFixed(1)}s`} />
                <Badge text={`${s.tokens_per_second?.toFixed(1) || '?'} t/s`} color="accent" />
                <span className="text-surface-400 text-xs">Core {s.core}</span>
              </div>
              <pre className="bg-surface-900 text-xs text-surface-300 p-3 rounded overflow-x-auto max-h-60">{s.output}</pre>
            </div>
          ))}

          {/* Sandbox */}
          {result.sandbox && (
            <div className={`bg-surface-800 rounded-lg p-4 border-l-2 ${result.sandbox.passed ? 'border-success' : 'border-danger'} space-y-2`}>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">Sandbox</span>
                <Badge text={result.sandbox.passed ? 'PASSED' : 'FAILED'} color={result.sandbox.passed ? 'success' : 'danger'} />
              </div>
              {result.sandbox.stderr && (
                <pre className="bg-surface-900 text-xs text-danger/80 p-3 rounded overflow-x-auto max-h-40">{result.sandbox.stderr}</pre>
              )}
              {result.sandbox.stdout && (
                <pre className="bg-surface-900 text-xs text-surface-300 p-3 rounded overflow-x-auto max-h-40">{result.sandbox.stdout}</pre>
              )}
            </div>
          )}

          {/* Merged output */}
          {result.merged_output && (
            <div className="bg-surface-800 rounded-lg p-4 space-y-2">
              <div className="font-semibold text-sm text-surface-300">Merged Output</div>
              <pre className="bg-surface-900 text-xs text-surface-300 p-3 rounded overflow-x-auto max-h-80">{result.merged_output}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
