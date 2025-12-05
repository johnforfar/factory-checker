import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'OpenxAI Base Mini App Explorer',
  description: 'Quality Assessment Dashboard for Mini App Factory Apps',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem', backgroundColor: 'white', color: 'black', margin: 0 }}>{children}</body>
    </html>
  )
}


