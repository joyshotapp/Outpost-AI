import type { Metadata } from "next"
import "@factory-insider/ui/globals.css"
import AdminShell from '../components/AdminShell'

export const metadata: Metadata = {
  title: "Admin Dashboard - Factory Insider",
  description: "Platform administration and analytics dashboard",
  viewport: "width=device-width, initial-scale=1",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="bg-gray-100 text-gray-900">
        <div id="root" className="min-h-screen">
          <AdminShell>{children}</AdminShell>
        </div>
      </body>
    </html>
  )
}
