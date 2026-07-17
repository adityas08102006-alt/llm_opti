import { NextRequest, NextResponse } from 'next/server'

// Allow up to 60s for long-running requests (Pro plan). Hobby max is 10s.
// For the generate endpoint, use POST /tasks (async) to avoid timeout.
export const maxDuration = 60

const BACKEND = 'http://3.107.210.17:9000'

export async function GET(request: NextRequest) {
  return proxy(request)
}

export async function POST(request: NextRequest) {
  return proxy(request)
}

async function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname.replace(/^\/api\//, '')
  const qs = request.nextUrl.search
  const body = request.method === 'POST' ? await request.text() : undefined
  const headers = new Headers(request.headers)
  headers.delete('host')

  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 55000)
    const res = await fetch(`${BACKEND}/${pathname}${qs}`, {
      method: request.method,
      headers,
      body,
      signal: controller.signal,
    })
    clearTimeout(timeout)
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'content-type': res.headers.get('content-type') || 'application/json' },
    })
  } catch {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 })
  }
}
