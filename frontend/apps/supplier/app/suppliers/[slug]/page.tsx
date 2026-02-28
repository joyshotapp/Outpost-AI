'use client'

import React, { useState } from 'react'
import Image from 'next/image'

interface SupplierProfilePageProps {
  params: {
    slug: string
  }
}

// Mock supplier data
const mockSupplier = {
  id: '1',
  companyName: 'ABC Manufacturing',
  companySlug: 'abc-manufacturing',
  website: 'https://abc-mfg.com',
  phone: '+86 10 1234 5678',
  email: 'contact@abc-mfg.com',
  country: 'China',
  city: 'Shanghai',
  address: '123 Industrial Park, Pudong District',
  industry: 'Electronics & Computing',
  mainProducts: 'Mechanical parts, CNC machining, fasteners',
  description: 'Leading manufacturer of precision mechanical parts for industrial applications with 20 years of experience.',
  employeeCount: '51-100',
  establishedYear: 2010,
  certifications: ['ISO 9001:2015', 'ISO 14001:2015', 'IATF 16949'],
  isVerified: true,
  logoUrl: 'https://via.placeholder.com/200x200',
  coverImageUrl: 'https://via.placeholder.com/1200x400',
  profileViews: 1234,
  responseRate: 92,
  responseTime: '2 hours',
  videos: [
    {
      id: '1',
      title: 'Company Overview',
      thumbnail: 'https://via.placeholder.com/400x300',
    },
    {
      id: '2',
      title: 'CNC Machining Process',
      thumbnail: 'https://via.placeholder.com/400x300',
    },
    {
      id: '3',
      title: 'Quality Control',
      thumbnail: 'https://via.placeholder.com/400x300',
    },
  ],
}

export default function SupplierProfilePage({ params }: SupplierProfilePageProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const supplier = mockSupplier

  return (
    <div className="bg-white">
      {/* Cover Image */}
      <div className="relative h-64 bg-gray-200 overflow-hidden">
        {supplier.coverImageUrl && (
          <Image
            src={supplier.coverImageUrl}
            alt="Cover"
            fill
            className="object-cover"
          />
        )}
      </div>

      {/* Profile Header */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 -mt-20 relative z-10">
        <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-end pb-6">
          {/* Logo */}
          {supplier.logoUrl && (
            <div className="relative w-40 h-40 bg-white rounded-lg shadow-lg overflow-hidden flex-shrink-0">
              <Image
                src={supplier.logoUrl}
                alt={supplier.companyName}
                fill
                className="object-contain p-4"
              />
            </div>
          )}

          {/* Company Info */}
          <div className="flex-1 pb-4">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-h1 font-bold text-gray-900">
                {supplier.companyName}
              </h1>
              {supplier.isVerified && (
                <span className="bg-green-100 text-green-800 text-body-xs font-medium px-3 py-1 rounded-full">
                  Verified
                </span>
              )}
            </div>
            <p className="text-body-lg text-gray-600 mb-4">
              {supplier.mainProducts}
            </p>

            {/* Stats */}
            <div className="flex flex-wrap gap-6 mb-4">
              <div>
                <p className="text-body-sm text-gray-600">Profile Views</p>
                <p className="text-h2 font-bold text-gray-900">{supplier.profileViews}</p>
              </div>
              <div>
                <p className="text-body-sm text-gray-600">Response Rate</p>
                <p className="text-h2 font-bold text-green-600">{supplier.responseRate}%</p>
              </div>
              <div>
                <p className="text-body-sm text-gray-600">Avg Response</p>
                <p className="text-h2 font-bold text-gray-900">{supplier.responseTime}</p>
              </div>
            </div>

            {/* Contact Button */}
            <button className="px-6 py-3 bg-primary-600 text-white text-body-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
              Send Inquiry
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <div className="flex gap-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'videos', label: 'Videos' },
              { id: 'products', label: 'Products & Services' },
              { id: 'reviews', label: 'Reviews' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`pb-4 text-body-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'text-primary-600 border-primary-600'
                    : 'text-gray-600 border-transparent hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              {/* Description */}
              <div>
                <h2 className="text-h2 font-semibold text-gray-900 mb-4">
                  About {supplier.companyName}
                </h2>
                <p className="text-body-base text-gray-700 leading-relaxed">
                  {supplier.description}
                </p>
              </div>

              {/* Company Info */}
              <div>
                <h2 className="text-h2 font-semibold text-gray-900 mb-4">
                  Company Information
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-body-sm text-gray-600">Industry</p>
                    <p className="text-body-base font-medium text-gray-900 mt-1">
                      {supplier.industry}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-body-sm text-gray-600">Founded</p>
                    <p className="text-body-base font-medium text-gray-900 mt-1">
                      {supplier.establishedYear}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-body-sm text-gray-600">Employees</p>
                    <p className="text-body-base font-medium text-gray-900 mt-1">
                      {supplier.employeeCount}
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-body-sm text-gray-600">Location</p>
                    <p className="text-body-base font-medium text-gray-900 mt-1">
                      {supplier.city}, {supplier.country}
                    </p>
                  </div>
                </div>
              </div>

              {/* Certifications */}
              <div>
                <h2 className="text-h2 font-semibold text-gray-900 mb-4">
                  Certifications
                </h2>
                <div className="flex flex-wrap gap-2">
                  {supplier.certifications.map((cert) => (
                    <span
                      key={cert}
                      className="inline-block px-4 py-2 bg-blue-50 border border-blue-200 text-blue-700 text-body-sm rounded-lg"
                    >
                      {cert}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Contact Info */}
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="text-body-lg font-semibold text-gray-900 mb-4">
                  Contact Information
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-body-sm text-gray-600">Email</p>
                    <a
                      href={`mailto:${supplier.email}`}
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {supplier.email}
                    </a>
                  </div>
                  <div>
                    <p className="text-body-sm text-gray-600">Phone</p>
                    <a
                      href={`tel:${supplier.phone}`}
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {supplier.phone}
                    </a>
                  </div>
                  <div>
                    <p className="text-body-sm text-gray-600">Website</p>
                    <a
                      href={supplier.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      Visit Website
                    </a>
                  </div>
                  <div>
                    <p className="text-body-sm text-gray-600">Address</p>
                    <p className="text-body-sm text-gray-900 mt-1">{supplier.address}</p>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="bg-gradient-to-br from-primary-50 to-blue-50 p-6 rounded-lg border border-primary-200">
                <h3 className="text-body-lg font-semibold text-gray-900 mb-4">
                  Supplier Rating
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-body-sm text-gray-600">Quality</span>
                      <span className="text-body-sm font-medium">4.8/5</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '96%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-body-sm text-gray-600">Reliability</span>
                      <span className="text-body-sm font-medium">4.9/5</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '98%' }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-body-sm text-gray-600">Communication</span>
                      <span className="text-body-sm font-medium">4.7/5</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-green-500 h-2 rounded-full" style={{ width: '94%' }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Videos Tab */}
        {activeTab === 'videos' && (
          <div>
            <h2 className="text-h2 font-semibold text-gray-900 mb-6">
              Product Videos
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {supplier.videos.map((video) => (
                <div
                  key={video.id}
                  className="group bg-white rounded-lg overflow-hidden shadow hover:shadow-lg transition-shadow cursor-pointer"
                >
                  <div className="relative w-full h-48 bg-gray-900 flex items-center justify-center overflow-hidden">
                    <Image
                      src={video.thumbnail}
                      alt={video.title}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform"
                    />
                    <button className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all">
                      <svg
                        className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                      </svg>
                    </button>
                  </div>
                  <div className="p-4">
                    <h3 className="text-body-sm font-semibold text-gray-900">
                      {video.title}
                    </h3>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Products & Services Tab */}
        {activeTab === 'products' && (
          <div>
            <h2 className="text-h2 font-semibold text-gray-900 mb-6">
              Products & Services
            </h2>
            <div className="bg-gray-50 p-8 rounded-lg text-center">
              <p className="text-body-base text-gray-600 mb-4">
                {supplier.mainProducts}
              </p>
              <button className="px-6 py-2 bg-primary-600 text-white text-body-sm font-medium rounded-lg hover:bg-primary-700 transition-colors">
                Request Catalog
              </button>
            </div>
          </div>
        )}

        {/* Reviews Tab */}
        {activeTab === 'reviews' && (
          <div>
            <h2 className="text-h2 font-semibold text-gray-900 mb-6">
              Customer Reviews
            </h2>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-gray-50 p-6 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">
                      Buyer {i} • Verified Purchase
                    </h3>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <svg
                          key={star}
                          className={`w-4 h-4 ${
                            star <= 5 ? 'text-yellow-400' : 'text-gray-300'
                          }`}
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      ))}
                    </div>
                  </div>
                  <p className="text-body-sm text-gray-700">
                    Great quality products and fast shipping. Highly recommend!
                  </p>
                  <p className="text-body-xs text-gray-500 mt-2">2 months ago</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
