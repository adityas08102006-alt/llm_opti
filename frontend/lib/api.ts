const KEY = process.env.NEXT_PUBLIC_API_KEY || ''

// Use the Vercel proxy path (/api) on HTTPS pages to avoid mixed content.
// Override with NEXT_PUBLIC_API_URL for local dev (e.g. http://localhost:9000).
const BASE = (() => {
  const base = process.env.NEXT_PUBLIC_API_URL || '/api'
  if (typeof window !== 'undefined' && window.location.protocol === 'https:' && base.startsWith('http://')) {
    return '/api'
  }
  return base
})()

interface FetchOptions extends RequestInit {
  params?: Record<string, string>
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...init } = options
  let url = `${BASE}${path}`
  if (params) {
    const qs = new URLSearchParams(params).toString()
    url += `?${qs}`
  }
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string>),
  }
  if (KEY) headers['Authorization'] = `Bearer ${KEY}`
  if (init.body && typeof init.body === 'string') {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 200)}`)
  }
  return res.json()
}

// ---------- typed responses ----------
export interface HealthResponse {
  status: string
}

export interface StatsResponse {
  llama_metrics: Record<string, Record<string, number>>
  cpu_percent: number[]
  total_requests: number
  sandbox_passes: number
  sandbox_fails: number
  last_generate_duration_ms: number
}

export interface ArmVerifyResponse {
  status: string
  neon: boolean
  dotprod: boolean
  i8mm: boolean
  sve: boolean
  kleidiai_build: boolean
  arm_arch: string | null
}

export interface VersionResponse {
  version: string
  models: { name: string; port: number; role: string }[]
  kleidiai: { enabled: boolean; arm_arch: string | null }
  python_version: string
  uptime_seconds: number
}

export interface SubtaskResult {
  subtask_id: number
  name: string
  model: string
  output: string
  tokens_per_second: number
  total_duration_ms: number
  core: string
}

export interface SandboxResult {
  passed: boolean
  stdout: string
  stderr: string
  returncode: number
  failure_kind: string | null
  duration_ms: number
}

export interface GenerateResponse {
  prompt: string
  dag_shape: string
  subtasks: SubtaskResult[]
  sandbox: SandboxResult | null
  regeneration_attempts: number
  fully_verified: boolean
  total_duration_ms: number
  merged_output: string
  cached?: boolean
}

// ---------- API methods ----------
export const api = {
  health: () => request<HealthResponse>('/health'),
  stats: () => request<StatsResponse>('/stats'),
  armVerify: () => request<ArmVerifyResponse>('/system/arm-verify'),
  version: () => request<VersionResponse>('/version'),
  generate: (prompt: string) =>
    request<GenerateResponse>('/generate', {
      method: 'POST',
      body: JSON.stringify({ prompt, demo_mode: 'live' }),
    }),
}
