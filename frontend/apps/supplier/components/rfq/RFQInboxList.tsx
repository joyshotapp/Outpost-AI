'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { RFQListItem } from './RFQListItem'

interface RFQData {
  id: number
  product_name: string
  buyer_company?: string
  lead_grade: 'A' | 'B' | 'C'
  lead_score: number
  description: string
  quantity: string
  created_at: string
  status: 'new' | 'viewed' | 'replied' | 'archived'
}

interface RFQInboxListProps {
  initialRFQs?: RFQData[]
  loading?: boolean
  onLoadMore?: () => void
}

export function RFQInboxList({
  initialRFQs = [],
  loading = false,
  onLoadMore,
}: RFQInboxListProps) {
  const t = useTranslations('rfq')
  const [rfqs, setRfqs] = useState<RFQData[]>(initialRFQs)
  const [filteredRFQs, setFilteredRFQs] = useState<RFQData[]>(initialRFQs)

  // Filter states
  const [filters, setFilters] = useState({
    grade: 'all',
    status: 'all',
    sortBy: 'newest',
  })

  // Pagination
  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const itemsPerPage = pageSize
  const totalPages = Math.ceil(filteredRFQs.length / itemsPerPage)
  const paginatedRFQs = filteredRFQs.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  )

  // Apply filters
  useEffect(() => {
    let result = [...rfqs]

    // Filter by grade
    if (filters.grade !== 'all') {
      result = result.filter(rfq => rfq.lead_grade === filters.grade)
    }

    // Filter by status
    if (filters.status !== 'all') {
      result = result.filter(rfq => rfq.status === filters.status)
    }

    // Sort
    switch (filters.sortBy) {
      case 'newest':
        result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        break
      case 'oldest':
        result.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        break
      case 'highest_score':
        result.sort((a, b) => b.lead_score - a.lead_score)
        break
      case 'lowest_score':
        result.sort((a, b) => a.lead_score - b.lead_score)
        break
    }

    setFilteredRFQs(result)
    setPage(1) // Reset to first page when filters change
  }, [rfqs, filters])

  const handleFilterChange = useCallback((filterName: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value,
    }))
  }, [])

  const handleClearFilters = useCallback(() => {
    setFilters({
      grade: 'all',
      status: 'all',
      sortBy: 'newest',
    })
  }, [])

  const isFiltered = filters.grade !== 'all' || filters.status !== 'all' || filters.sortBy !== 'newest'

  return (
    <div className="space-y-6">
      {/* Filters Section */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="space-y-4">
          {/* Filter Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Filters & Sort</h3>
            {isFiltered && (
              <button
                onClick={handleClearFilters}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                Clear All
              </button>
            )}
          </div>

          {/* Filter Controls */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Grade Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Lead Grade
              </label>
              <select
                value={filters.grade}
                onChange={e => handleFilterChange('grade', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Grades</option>
                <option value="A">Grade A - High Quality</option>
                <option value="B">Grade B - Medium Quality</option>
                <option value="C">Grade C - Low Quality</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={filters.status}
                onChange={e => handleFilterChange('status', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Status</option>
                <option value="new">New</option>
                <option value="viewed">Viewed</option>
                <option value="replied">Replied</option>
                <option value="archived">Archived</option>
              </select>
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={filters.sortBy}
                onChange={e => handleFilterChange('sortBy', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="highest_score">Highest Score</option>
                <option value="lowest_score">Lowest Score</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          Showing <span className="font-semibold">{paginatedRFQs.length}</span> of{' '}
          <span className="font-semibold">{filteredRFQs.length}</span> RFQs
          {isFiltered && ' (filtered)'}
        </p>
      </div>

      {/* RFQ List */}
      {filteredRFQs.length === 0 ? (
        <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <div className="text-4xl mb-4">📭</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No RFQs Found</h3>
          <p className="text-gray-600">
            {isFiltered
              ? 'Try adjusting your filters to find RFQs'
              : 'No RFQs in your inbox yet. Check back soon!'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {paginatedRFQs.map(rfq => (
            <RFQListItem
              key={rfq.id}
              id={rfq.id}
              product_name={rfq.product_name}
              buyer_company={rfq.buyer_company}
              lead_grade={rfq.lead_grade}
              lead_score={rfq.lead_score}
              description={rfq.description}
              quantity={rfq.quantity}
              created_at={rfq.created_at}
              status={rfq.status}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between py-4">
          <div className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(prev => Math.max(1, prev - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
            >
              Next
            </button>
          </div>
          {onLoadMore && page === totalPages && (
            <button
              onClick={onLoadMore}
              disabled={loading}
              className="px-4 py-2 border border-primary-300 text-primary-700 rounded-md hover:bg-primary-50 disabled:opacity-50 font-medium text-sm"
            >
              {loading ? 'Loading...' : 'Load More'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
