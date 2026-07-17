'use client'

import { usePathname } from 'next/navigation'
import Sidebar from '@/components/Layout/Sidebar'
import Header from '@/components/Layout/Header'
import { useLiveMetrics } from '@/hooks/useLiveMetrics'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/runs': 'Runs',
  '/models': 'Models',
  '/benchmarks': 'Benchmarks',
  '/metrics': 'Metrics',
  '/health': 'Health',
  '/system': 'System',
  '/settings': 'Settings',
}

export default function ClientShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { version } = useLiveMetrics(30000)
  const healthy = version !== null

  return (
    <div className="flex h-full">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header title={titles[pathname] || 'LLM Opti'} healthy={healthy} version={version?.version ?? null} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  )
}
