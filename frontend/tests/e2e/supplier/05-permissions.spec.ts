import { test, expect, BACKEND } from '../fixtures'

test.describe('API Permission Matrix', () => {
  test('protected endpoints deny unauthenticated access', async () => {
    const targets = [
      `${BACKEND}/api/v1/rfqs`,
      `${BACKEND}/api/v1/admin/kpi/overview`,
    ]

    for (const url of targets) {
      const res = await fetch(url)
      expect([401, 403], `Unauthenticated should be denied: ${url}`).toContain(res.status)
    }
  })

  test('malformed token is rejected', async () => {
    const res = await fetch(`${BACKEND}/api/v1/rfqs`, {
      headers: { Authorization: 'Bearer not-a-real-token' },
    })
    expect([401, 403], 'Malformed JWT should be rejected').toContain(res.status)
  })

  test('buyer can create RFQ, supplier cannot create RFQ', async ({ buyerToken, supplierToken }) => {
    const payload = new FormData()
    payload.append('title', `Permission Matrix RFQ ${Date.now()}`)
    payload.append('description', 'Role based permission test payload')
    payload.append('quantity', '10')
    payload.append('unit', 'pcs')

    const buyerRes = await fetch(`${BACKEND}/api/v1/rfqs`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${buyerToken}` },
      body: payload,
    })
    expect([200, 201], 'Buyer should be able to create RFQ').toContain(buyerRes.status)

    const supplierPayload = new FormData()
    supplierPayload.append('title', `Supplier forbidden RFQ ${Date.now()}`)
    supplierPayload.append('description', 'Supplier should not create buyer RFQ')

    const supplierRes = await fetch(`${BACKEND}/api/v1/rfqs`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${supplierToken}` },
      body: supplierPayload,
    })
    expect(supplierRes.status, 'Supplier creating RFQ should be forbidden').toBe(403)
  })

  test('buyer cannot access admin KPI endpoint', async ({ buyerToken }) => {
    const res = await fetch(`${BACKEND}/api/v1/admin/kpi/overview`, {
      headers: { Authorization: `Bearer ${buyerToken}` },
    })
    expect([401, 403], 'Buyer should not access admin KPI').toContain(res.status)
  })

  test('supplier cannot read buyer-owned RFQ detail', async ({ buyerToken, supplierToken }) => {
    const payload = new FormData()
    payload.append('title', `Ownership RFQ ${Date.now()}`)
    payload.append('description', 'Ownership check between buyer and supplier')

    const createRes = await fetch(`${BACKEND}/api/v1/rfqs`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${buyerToken}` },
      body: payload,
    })
    expect([200, 201]).toContain(createRes.status)
    const created = await createRes.json()

    const detailRes = await fetch(`${BACKEND}/api/v1/rfqs/${created.id}`, {
      headers: { Authorization: `Bearer ${supplierToken}` },
    })
    expect([401, 403], 'Supplier should not read unassigned buyer RFQ').toContain(detailRes.status)
  })
})
