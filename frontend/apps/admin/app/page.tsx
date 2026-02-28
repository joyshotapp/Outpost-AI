export default function AdminDashboard() {
  return (
    <main className="w-full">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="text-h2 font-bold text-primary-700">
            Admin Dashboard
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
              { label: "Suppliers", badge: 245 },
              { label: "Buyers", badge: 1230 },
              { label: "RFQ Inquiries", badge: 89 },
              { label: "Analytics" },
              { label: "Settings" },
            ].map((item, index) => (
              <a
                key={index}
                href="#"
                className={`block px-4 py-2 rounded-md font-medium transition-colors flex justify-between items-center ${
                  item.active
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                {item.label}
                {item.badge && (
                  <span className="text-body-sm bg-primary-700 text-white px-2 py-1 rounded-full">
                    {item.badge}
                  </span>
                )}
              </a>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 p-8">
          <h1 className="text-h2 font-bold mb-6">Platform Overview</h1>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[
              { label: "Total Users", value: "1,475", change: "+12%" },
              { label: "Active Suppliers", value: "245", change: "+5%" },
              { label: "Monthly Revenue", value: "$156,230", change: "+23%" },
              { label: "Platform Health", value: "99.8%", change: "✓" },
            ].map((kpi, index) => (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6"
              >
                <p className="text-body-sm text-gray-600 mb-2">{kpi.label}</p>
                <p className="text-h2 font-bold text-gray-900 mb-2">{kpi.value}</p>
                <p className={`text-body-sm font-medium ${
                  kpi.change.includes("+") ? "text-success-700" : "text-primary-700"
                }`}>
                  {kpi.change}
                </p>
              </div>
            ))}
          </div>

          {/* System Status */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Services Health */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-h3 font-semibold mb-4">Services Health</h2>
              <div className="space-y-3">
                {[
                  { service: "API", status: "healthy" },
                  { service: "Database", status: "healthy" },
                  { service: "Redis", status: "healthy" },
                  { service: "Elasticsearch", status: "healthy" },
                ].map((item, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center p-3 bg-gray-50 rounded"
                  >
                    <span className="font-medium">{item.service}</span>
                    <span className="text-body-sm px-3 py-1 bg-success-100 text-success-700 rounded-full">
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 lg:col-span-2">
              <h2 className="text-h3 font-semibold mb-4">Recent Activity</h2>
              <div className="space-y-3">
                {[
                  "New supplier registered: ABC Manufacturing",
                  "RFQ inquiries exceeded 50 for the day",
                  "Platform maintenance scheduled for 2026-03-01",
                  "New API integration: HubSpot CRM",
                ].map((activity, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 rounded border-l-4 border-primary-700"
                  >
                    <p className="text-body text-gray-700">{activity}</p>
                    <p className="text-body-sm text-gray-500 mt-1">2 hours ago</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
