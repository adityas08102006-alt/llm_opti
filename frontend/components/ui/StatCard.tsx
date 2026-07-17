'use client'

interface StatCardProps {
  label: string
  value: React.ReactNode
  sub?: string
  color?: 'default' | 'success' | 'warning' | 'danger'
}

const colorMap = {
  default: 'text-surface-200',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

export default function StatCard({ label, value, sub, color = 'default' }: StatCardProps) {
  return (
    <div className="bg-surface-800 rounded-lg p-4 text-center">
      <div className="text-xs text-surface-400 uppercase tracking-wide">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${colorMap[color]}`}>{value}</div>
      {sub && <div className="text-xs text-surface-400 mt-1">{sub}</div>}
    </div>
  )
}
