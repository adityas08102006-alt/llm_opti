interface BadgeProps {
  text: string
  color?: 'neutral' | 'success' | 'warning' | 'danger' | 'accent'
}

const colors = {
  neutral: 'bg-surface-700 text-surface-300',
  success: 'bg-success/20 text-success',
  warning: 'bg-warning/20 text-warning',
  danger: 'bg-danger/20 text-danger',
  accent: 'bg-accent-500/20 text-accent-400',
}

export default function Badge({ text, color = 'neutral' }: BadgeProps) {
  return (
    <span className={`inline-block px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${colors[color]}`}>
      {text}
    </span>
  )
}
