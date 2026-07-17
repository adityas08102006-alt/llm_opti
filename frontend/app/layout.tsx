import type { Metadata } from 'next'
import { Suspense } from 'react'
import './globals.css'
import ClientShell from './client-shell'

export const metadata: Metadata = {
  title: 'LLM Opti — Control Panel',
  description: 'Parallel Task Decomposition Engine Dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full" suppressHydrationWarning>
        <Suspense fallback={<div className="flex h-full items-center justify-center text-surface-400">Loading…</div>}>
          <ClientShell>{children}</ClientShell>
        </Suspense>
      </body>
    </html>
  )
}
