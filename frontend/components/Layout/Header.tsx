'use client'

import Badge from '@/components/ui/Badge'

interface HeaderProps {
  title: string
  healthy: boolean
  version: string | null
}

export default function Header({ title, healthy, version }: HeaderProps) {
  return (
    <header className="h-14 bg-surface-800 border-b border-surface-700 flex items-center justify-between px-6 shrink-0">
      <h1 className="text-lg font-semibold text-surface-100">{title}</h1>
      <div className="flex items-center gap-3 text-xs text-surface-400">
        {version && <span>v{version}</span>}
        <Badge text={healthy ? 'connected' : 'disconnected'} color={healthy ? 'success' : 'danger'} />
      </div>
    </header>
  )
}
