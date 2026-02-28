import type { Metadata } from "next"
import "@factory-insider/ui/globals.css"

export const metadata: Metadata = {
  title: "Supplier Dashboard - Factory Insider",
  description: "Manage your supplier profile, showcase products, and track buyer inquiries",
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
        <div id="root" className="min-h-screen">{children}</div>
      </body>
    </html>
  )
}
