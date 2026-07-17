export default function Spinner({ className = '' }: { className?: string }) {
  return (
    <div className={`border-2 border-surface-700 border-t-accent-500 rounded-full w-6 h-6 animate-spin ${className}`} />
  )
}
