import { MetadataRoute } from 'next'

/**
 * Dynamic sitemap for Factory Insider buyer app.
 * Sprint 10 — SEO: statically export core routes + placeholder for
 * dynamic supplier pages (real implementation will query DB/API).
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://factoryinsider.com'
  const now = new Date().toISOString()

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: `${BASE_URL}/`,
      lastModified: now,
      changeFrequency: 'daily',
      priority: 1.0,
    },
    {
      url: `${BASE_URL}/suppliers`,
      lastModified: now,
      changeFrequency: 'hourly',
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/rfq/new`,
      lastModified: now,
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/dashboard`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.5,
    },
  ]

  // Dynamic supplier pages — in production this would fetch from DB/API
  // Example (uncomment and adapt when API is running):
  //
  // let supplierPages: MetadataRoute.Sitemap = []
  // try {
  //   const res = await fetch(`${process.env.API_URL}/api/v1/suppliers?page_size=500&is_active=true`)
  //   if (res.ok) {
  //     const { suppliers } = await res.json()
  //     supplierPages = suppliers.map((s: { company_slug: string; updated_at: string }) => ({
  //       url: `${BASE_URL}/suppliers/${s.company_slug}`,
  //       lastModified: s.updated_at || now,
  //       changeFrequency: 'weekly' as const,
  //       priority: 0.8,
  //     }))
  //   }
  // } catch { /* non-fatal */ }

  return [...staticPages]
}
