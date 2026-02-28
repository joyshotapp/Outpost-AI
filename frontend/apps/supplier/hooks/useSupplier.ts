import { useState, useCallback } from 'react'

export interface SupplierData {
  id?: string
  companyName: string
  companySlug: string
  website?: string
  phone: string
  email: string
  country: string
  city: string
  address?: string
  postalCode?: string
  industry: string
  mainProducts: string
  description?: string
  employeeCount?: string
  establishedYear?: number
  certifications: string[]
  businessLicense?: string
  taxId?: string
  bankDetails?: string
  logoUrl?: string
  coverImageUrl?: string
  isVerified?: boolean
}

interface UseSupplierReturn {
  supplier: SupplierData | null
  loading: boolean
  error: string | null
  fetchSupplier: (id: string) => Promise<void>
  updateSupplier: (data: Partial<SupplierData>) => Promise<void>
  uploadLogo: (file: File) => Promise<string>
  uploadCoverImage: (file: File) => Promise<string>
  uploadGalleryImages: (files: File[]) => Promise<string[]>
}

export const useSupplier = (): UseSupplierReturn => {
  const [supplier, setSupplier] = useState<SupplierData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSupplier = useCallback(async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/v1/suppliers/${id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch supplier')
      }
      const data = await response.json()
      setSupplier(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [])

  const updateSupplier = useCallback(async (data: Partial<SupplierData>) => {
    if (!supplier?.id) {
      setError('No supplier ID found')
      return
    }

    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/v1/suppliers/${supplier.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to update supplier')
      }

      const updated = await response.json()
      setSupplier(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      throw err
    } finally {
      setLoading(false)
    }
  }, [supplier?.id])

  const uploadFile = useCallback(
    async (file: File, fileType: 'logo' | 'cover' | 'gallery') => {
      if (!supplier?.id) {
        throw new Error('No supplier ID found')
      }

      try {
        // Step 1: Request presigned URL
        const presignedResponse = await fetch('/api/v1/uploads/presigned-url', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: file.name,
            content_type: file.type,
            resource_type: fileType,
            file_size: file.size,
          }),
        })

        if (!presignedResponse.ok) {
          throw new Error('Failed to get presigned URL')
        }

        const { url, fields } = await presignedResponse.json()

        // Step 2: Upload file to S3 using presigned POST (multipart form data)
        const formData = new FormData()
        Object.entries(fields as Record<string, string>).forEach(([key, value]) => {
          formData.append(key, value)
        })
        formData.append('file', file)

        const uploadResponse = await fetch(url, {
          method: 'POST',
          body: formData,
        })

        if (!uploadResponse.ok) {
          throw new Error('Failed to upload file to S3')
        }

        // Step 3: Verify upload and get the final download URL
        const object_key = fields['key'] as string
        const verifyResponse = await fetch('/api/v1/uploads/status', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ object_key }),
        })

        if (!verifyResponse.ok) {
          throw new Error('Failed to verify upload')
        }

        const { download_url } = await verifyResponse.json()
        return download_url as string
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed')
        throw err
      }
    },
    [supplier?.id]
  )

  const uploadLogo = useCallback(
    (file: File) => uploadFile(file, 'logo'),
    [uploadFile]
  )

  const uploadCoverImage = useCallback(
    (file: File) => uploadFile(file, 'cover'),
    [uploadFile]
  )

  const uploadGalleryImages = useCallback(
    async (files: File[]) => {
      const urls: string[] = []
      for (const file of files) {
        const url = await uploadFile(file, 'gallery')
        urls.push(url)
      }
      return urls
    },
    [uploadFile]
  )

  return {
    supplier,
    loading,
    error,
    fetchSupplier,
    updateSupplier,
    uploadLogo,
    uploadCoverImage,
    uploadGalleryImages,
  }
}
