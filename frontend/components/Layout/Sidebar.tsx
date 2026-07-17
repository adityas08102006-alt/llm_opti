'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const links = [
  { href: '/', label: 'Dashboard', icon: '◉' },
  { href: '/runs', label: 'Runs', icon: '▶' },
  { href: '/models', label: 'Models', icon: '◇' },
  { href: '/benchmarks', label: 'Benchmarks', icon: '■' },
  { href: '/metrics', label: 'Metrics', icon: '⏱' },
  { href: '/health', label: 'Health', icon: '◆' },
  { href: '/system', label: 'System', icon: '⚙' },
  { href: '/settings', label: 'Settings', icon: '⚛' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-56 bg-surface-800 border-r border-surface-700 flex flex-col shrink-0">
      <div className="h-14 flex items-center px-5 border-b border-surface-700">
        <span className="text-accent-400 font-bold text-sm uppercase tracking-widest">LLM Opti</span>
      </div>
      <nav className="flex-1 py-3 space-y-0.5 overflow-y-auto">
        {links.map((l) => {
          const active = pathname === l.href
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`flex items-center gap-3 px-5 py-2.5 text-sm transition-colors ${
                active
                  ? 'bg-accent-500/10 text-accent-400 border-r-2 border-accent-500'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-700/50'
              }`}
            >
              <span className="text-base w-5 text-center">{l.icon}</span>
              {l.label}
            </Link>
          )
        })}
      </nav>
      <div className="p-4 border-t border-surface-700 text-[10px] text-surface-600 leading-relaxed">
        v2.0.0 &middot; Graviton3<br />
        KleidiAI &middot; Arm64
      </div>
    </aside>
  )
}
