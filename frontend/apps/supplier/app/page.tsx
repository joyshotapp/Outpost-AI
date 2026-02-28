export default function SupplierDashboard() {
  return (
    <main className="w-full">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="text-h2 font-bold text-primary-700">
            Supplier Dashboard
          </div>
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
          </div>
        </div>
      </header>

      {/* Sidebar + Content */}
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-screen p-6">
          <nav className="space-y-2">
            {[
              { label: "Dashboard", active: true },
              { label: "Profile" },
              { label: "Products" },
              { label: "RFQ Inquiries" },
              { label: "Analytics" },
              { label: "Settings" },
            ].map((item, index) => (
              <a
                key={index}
                href="#"
                className={`block px-4 py-2 rounded-md font-medium transition-colors ${
                  item.active
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                {item.label}
              </a>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 p-8">
          <h1 className="text-h2 font-bold mb-6">Welcome to Your Dashboard</h1>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[
              { label: "Total Views", value: "1,234" },
              { label: "Active RFQs", value: "12" },
              { label: "Response Rate", value: "94%" },
              { label: "This Month Revenue", value: "$24,532" },
            ].map((stat, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6"
              >
                <p className="text-body-sm text-gray-600 mb-2">{stat.label}</p>
                <p className="text-h2 font-bold text-gray-900">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Recent RFQs */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-h3 font-semibold mb-4">Recent Inquiries</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      Inquiry ID
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      From
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[1, 2, 3].map((_, index) => (
                    <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">RFQ-001{index + 1}</td>
                      <td className="py-3 px-4">Company Inc.</td>
                      <td className="py-3 px-4">
                        <span className="px-3 py-1 bg-success-100 text-success-700 rounded-full text-body-sm font-medium">
                          Pending
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-600">2026-02-28</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
