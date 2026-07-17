import type { Metadata } from 'next'
import './globals.css'
import ClientShell from './client-shell'

export const metadata: Metadata = {
  title: 'LLM Opti — Control Panel',
  description: 'Parallel Task Decomposition Engine Dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full">
        <ClientShell>{children}</ClientShell>
      </body>
    </html>
  )
}
