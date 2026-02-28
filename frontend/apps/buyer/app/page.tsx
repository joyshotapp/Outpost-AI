'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex-1 w-full">
      {/* Header */}
      <header className="border-b border-gray-200">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="text-h2 font-bold text-primary-700">
            Factory Insider
          </div>
          <div className="space-x-4">
            <button className="px-6 py-2 text-primary-700 hover:text-primary-900 font-medium">
              Login
            </button>
            <button className="px-6 py-2 bg-primary-700 text-white rounded-md hover:bg-primary-600 font-medium">
              Sign Up
            </button>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-100 to-primary-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-h1 font-bold text-gray-900 mb-6">
                Find Verified Suppliers Worldwide
              </h1>
              <p className="text-body-lg text-gray-700 mb-8">
                Connect with pre-screened manufacturers and suppliers. Get instant
                quotes, compare options, and source products faster with AI-powered
                intelligence.
              </p>
              <div className="flex gap-4">
                <Link
                  href="/rfq/new"
                  className="px-8 py-4 bg-primary-700 text-white rounded-md hover:bg-primary-600 font-semibold inline-block text-center"
                >
                  Create RFQ
                </Link>
                <button className="px-8 py-4 border-2 border-primary-700 text-primary-700 rounded-md hover:bg-primary-50 font-semibold">
                  View Demo
                </button>
              </div>
            </div>
            <div className="bg-gray-200 rounded-lg h-96 flex items-center justify-center">
              <p className="text-gray-500">Supplier Showcase</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-h2 font-bold text-center mb-12">Why Choose Factory Insider?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: "AI-Powered Matching",
                description: "Our AI analyzes your requirements and matches you with the best suppliers",
              },
              {
                title: "Verified Suppliers",
                description: "All suppliers are pre-screened and verified for quality and reliability",
              },
              {
                title: "24/7 Support",
                description: "Get answers instantly from our AI assistant in your language",
              },
            ].map((feature, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                <h3 className="text-h3 font-semibold mb-3">{feature.title}</h3>
                <p className="text-body text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-700 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-h2 font-bold mb-6">Ready to Find Your Next Supplier?</h2>
          <p className="text-body-lg mb-8">
            Join thousands of buyers sourcing from verified suppliers
          </p>
          <Link
            href="/rfq/new"
            className="inline-block px-8 py-4 bg-white text-primary-700 rounded-md hover:bg-gray-100 font-semibold"
          >
            Create Your First RFQ
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-body-sm text-gray-400">
          <p>&copy; 2026 Factory Insider. All rights reserved.</p>
        </div>
      </footer>
    </main>
  )
}
