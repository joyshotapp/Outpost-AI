'use client'

import React from 'react'
import Link from 'next/link'

interface StatCard {
  label: string
  value: string | number
  icon: React.ReactNode
  href?: string
  trend?: 'up' | 'down'
  trendValue?: string
}

const stats: StatCard[] = [
  {
    label: 'Total Inquiries',
    value: 24,
    href: '/dashboard/inquiries',
    trend: 'up',
    trendValue: '+12% this month',
    icon: (
      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path d="M2.5 3A1.5 1.5 0 001 4.5v.793c.026.009.051.02.076.032a.75.75 0 00.658.482 60.456 60.456 0 014.064-.053.75.75 0 00.658-.482c.025-.012.05-.023.076-.032V4.5A1.5 1.5 0 002.5 3zM1 7.75V19.5A1.5 1.5 0 002.5 21h15A1.5 1.5 0 0019 19.5V7.75c-.345.104-.681.227-1 .367V19.5H2.5V7.75c-.319-.14-.655-.263-1-.367z" />
      </svg>
    ),
  },
  {
    label: 'Active Orders',
    value: 8,
    href: '/dashboard/orders',
    trend: 'up',
    trendValue: '+2 this week',
    icon: (
      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.5.5 0 00.487.358h12.382a.5.5 0 00.494-.574l-2-10A.5.5 0 0015.35 3H4.196a.5.5 0 00-.487.358L2.293 2H1a1 1 0 000 2h1l3.355 16.954a.5.5 0 00.487.358h10.516a.5.5 0 00.487-.358L17.707 5H16a1 1 0 100-2h1.293l-.305-1.222A.5.5 0 0015.382 1H3z" />
      </svg>
    ),
  },
  {
    label: 'Product Videos',
    value: 12,
    href: '/dashboard/videos',
    trend: 'up',
    trendValue: '+3 new videos',
    icon: (
      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
      </svg>
    ),
  },
  {
    label: 'Profile Views',
    value: 342,
    href: '/dashboard/analytics',
    trend: 'up',
    trendValue: '+28% vs last month',
    icon: (
      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
      </svg>
    ),
  },
]

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-h1 font-bold text-gray-900">Dashboard</h1>
        <p className="text-body-lg text-gray-600 mt-2">
          Welcome back! Here's what's happening with your business today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Link
            key={stat.label}
            href={stat.href || '#'}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="text-primary-600 bg-primary-50 p-3 rounded-lg">
                {stat.icon}
              </div>
              {stat.trend && (
                <div
                  className={`text-xs font-medium px-2 py-1 rounded-full ${
                    stat.trend === 'up'
                      ? 'bg-green-50 text-green-700'
                      : 'bg-red-50 text-red-700'
                  }`}
                >
                  {stat.trend === 'up' ? '↑' : '↓'} {stat.trendValue}
                </div>
              )}
            </div>
            <p className="text-body-sm text-gray-600 mb-1">{stat.label}</p>
            <p className="text-h2 font-bold text-gray-900">{stat.value}</p>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Inquiries */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-h2 font-semibold text-gray-900">
              Recent Inquiries
            </h2>
            <Link
              href="/dashboard/inquiries"
              className="text-primary-600 text-body-sm font-medium hover:text-primary-700"
            >
              View all
            </Link>
          </div>
          <div className="space-y-4">
            {/* Inquiry Item */}
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <p className="text-body-sm font-medium text-gray-900">
                    Inquiry #{1000 + i}
                  </p>
                  <p className="text-body-xs text-gray-600 mt-1">
                    {['Electronics buyer', 'Manufacturing parts', 'Raw materials'][i - 1]}
                  </p>
                </div>
                <div className="text-right">
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-body-xs font-medium ${
                      ['bg-yellow-50 text-yellow-700', 'bg-blue-50 text-blue-700', 'bg-green-50 text-green-700'][
                        i - 1
                      ]
                    }`}
                  >
                    {['Pending', 'In Review', 'Quoted'][i - 1]}
                  </span>
                  <p className="text-body-xs text-gray-500 mt-2">2 days ago</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-h2 font-semibold text-gray-900 mb-6">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <Link
              href="/dashboard/profile"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">
                  Edit Profile
                </p>
                <p className="text-body-xs text-gray-500">Update company info</p>
              </div>
            </Link>

            <Link
              href="/dashboard/videos"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm4 2v4h8V8H6z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">
                  Upload Video
                </p>
                <p className="text-body-xs text-gray-500">Add product videos</p>
              </div>
            </Link>

            <Link
              href="/dashboard/inquiries"
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div className="text-primary-600 group-hover:text-primary-700">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.5 3A1.5 1.5 0 001 4.5v.793c.026.009.051.02.076.032a.75.75 0 00.658.482 60.456 60.456 0 014.064-.053.75.75 0 00.658-.482c.025-.012.05-.023.076-.032V4.5A1.5 1.5 0 002.5 3zM1 7.75V19.5A1.5 1.5 0 002.5 21h15A1.5 1.5 0 0019 19.5V7.75c-.345.104-.681.227-1 .367V19.5H2.5V7.75c-.319-.14-.655-.263-1-.367z" />
                </svg>
              </div>
              <div>
                <p className="text-body-sm font-medium text-gray-900">
                  View Inquiries
                </p>
                <p className="text-body-xs text-gray-500">Check buyer requests</p>
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Announcement Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zm-11-1a1 1 0 11-2 0 1 1 0 012 0zM8 8a1 1 0 000 2h6a1 1 0 100-2H8zm0 3a1 1 0 000 2h3a1 1 0 100-2H8z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-body-lg font-semibold text-blue-900">
              Announcement
            </h3>
            <p className="text-body-sm text-blue-800 mt-1">
              We've launched new analytics features! View detailed insights about your profile
              performance, buyer interactions, and more.
            </p>
            <Link
              href="/dashboard/analytics"
              className="inline-block mt-3 text-body-sm font-medium text-blue-600 hover:text-blue-700"
            >
              Learn more →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
