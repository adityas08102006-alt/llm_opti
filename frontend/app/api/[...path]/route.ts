import { NextRequest, NextResponse } from 'next/server'

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
    const res = await fetch(`${BACKEND}/${pathname}${qs}`, {
      method: request.method,
      headers,
      body,
    })
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'content-type': res.headers.get('content-type') || 'application/json' },
    })
  } catch {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 })
  }
}
