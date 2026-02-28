import type { Metadata } from "next"
import "@factory-insider/ui/globals.css"

export const metadata: Metadata = {
  title: "Factory Insider - Find Suppliers",
  description:
    "AI-powered B2B manufacturing marketplace connecting global buyers with suppliers",
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://factoryinsider.com",
    title: "Factory Insider",
    description: "Find verified suppliers worldwide",
    images: [
      {
        url: "https://factoryinsider.com/og-image.png",
        width: 1200,
        height: 630,
        alt: "Factory Insider",
      },
    ],
  },
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
      <body className="bg-white text-gray-900">
        <div id="root" className="min-h-screen flex flex-col">
          {children}
        </div>
      </body>
    </html>
  )
}
