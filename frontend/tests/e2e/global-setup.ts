/**
 * Global setup — seed realistic test data into the backend DB
 *
 * Runs ONCE before all tests. Ensures:
 *   1. Supplier user + profile exist
 *   2. Buyer user exists
 *   3. At least 3 RFQs with different grades
 *   4. Outbound campaign with contacts
 *   5. Exhibition record
 *
 * Idempotent — safe to run multiple times.
 */

const BACKEND = 'http://localhost:8001';

async function api(method: string, path: string, body?: unknown, token?: string) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BACKEND}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, data: await res.json().catch(() => null) };
}

async function login(email: string, password: string): Promise<string | null> {
  const { status, data } = await api('POST', '/api/v1/auth/login', { email, password });
  return status === 200 ? data.access_token : null;
}

async function ensureUser(email: string, password: string, role: string, name: string, company: string) {
  let token = await login(email, password);
  if (token) return token;
  const { status, data } = await api('POST', '/api/v1/auth/register', {
    email,
    password,
    role,
    full_name: name,
    company_name: company,
  });
  if (status === 201 || status === 200) {
    token = await login(email, password);
  }
  return token;
}

export default async function globalSetup() {
  console.log('[seed] Starting global setup...');

  // ── 1. Supplier ──────────────────────────────────────
  const supplierToken = await ensureUser(
    'test@factory.com',
    'Test1234!',
    'supplier',
    'Test Admin',
    'Taiwan Precision Parts Co.',
  );
  if (!supplierToken) {
    console.error('[seed] Could not get supplier token!');
    return;
  }
  console.log('[seed] Supplier ready');

  // Ensure supplier profile
  const { status: profStatus } = await api('GET', '/api/v1/suppliers/me', undefined, supplierToken);
  if (profStatus === 404) {
    await api(
      'POST',
      '/api/v1/suppliers',
      {
        company_name: 'Taiwan Precision Parts Co.',
        description: 'ISO 9001 & AS9100D certified CNC machining factory',
        country: 'TW',
        city: 'Taichung',
        capabilities: ['CNC Machining', '5-Axis Milling', 'Surface Treatment'],
        industries: ['Aerospace', 'Automotive', 'Medical'],
        certifications: ['ISO 9001', 'AS9100D', 'IATF 16949'],
        min_order_value: 5000,
        employee_count: 120,
        year_established: 2005,
        website: 'https://taiwan-precision.example.com',
      },
      supplierToken,
    );
    console.log('[seed] Supplier profile created');
  }

  // ── 2. Buyer ─────────────────────────────────────────
  const buyerToken = await ensureUser(
    'buyer@aerospace.de',
    'Buyer5678!',
    'buyer',
    'Klaus Weber',
    'Weber Aerospace GmbH',
  );
  if (!buyerToken) {
    console.error('[seed] Could not get buyer token!');
    return;
  }
  console.log('[seed] Buyer ready');

  // ── 3. RFQs ──────────────────────────────────────────
  const rfqPayloads = [
    {
      title: 'Precision Aluminum Brackets AS9100D Aircraft',
      description:
        'We require CNC machined 6061-T6 aluminum brackets for aircraft seat mounting. Annual volume 50000 pcs. Tolerances +/-0.01mm. Surface finish: Anodized. Certifications required: AS9100D. Material cert and FAIR required.',
      quantity: 50000,
      budget_min: 100000,
      budget_max: 250000,
    },
    {
      title: 'Stainless Steel Medical Implant Components',
      description:
        'Need 316L stainless steel micro-machined components for orthopedic implants. FDA Class III. Tolerances +/-0.005mm. Ra 0.4 surface finish. Annual volume 10000 sets.',
      quantity: 10000,
      budget_min: 200000,
      budget_max: 500000,
    },
    {
      title: 'Plastic Injection Molding Prototypes',
      description: 'Quick-turn prototyping for ABS housing. 50 units needed in 2 weeks. No special certs.',
      quantity: 50,
      budget_min: 500,
      budget_max: 2000,
    },
  ];

  // Check existing RFQs
  const { data: existingRfqs } = await api('GET', '/api/v1/rfqs', undefined, supplierToken);
  const existingCount = Array.isArray(existingRfqs) ? existingRfqs.length : 0;

  if (existingCount < 3) {
    for (const rfq of rfqPayloads.slice(existingCount)) {
      // RFQ creation endpoint requires multipart/form-data; use raw fetch
      const formData = new FormData();
      Object.entries(rfq).forEach(([k, v]) => formData.append(k, String(v)));
      const res = await fetch(`${BACKEND}/api/v1/rfqs`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${buyerToken}` },
        body: formData,
      });
      console.log(`[seed] RFQ "${rfq.title}" → ${res.status}`);
    }
  } else {
    console.log(`[seed] ${existingCount} RFQs already exist, skipping`);
  }

  // ── 4. Outbound Campaign ─────────────────────────────
  const { data: campaigns } = await api('GET', '/api/v1/outbound/campaigns', undefined, supplierToken);
  if (!Array.isArray(campaigns) || campaigns.length === 0) {
    await api(
      'POST',
      '/api/v1/outbound/campaigns',
      {
        campaign_name: 'E2E Test — Aerospace Buyers Outreach',
        campaign_type: 'linkedin',
        icp_criteria: {
          industries: ['Aerospace', 'Defense'],
          countries: ['DE', 'FR', 'UK'],
          job_titles: ['Procurement Manager', 'Supply Chain Director'],
          limit: 50,
        },
      },
      supplierToken,
    );
    console.log('[seed] Outbound campaign created');
  }

  // ── 5. Exhibition ────────────────────────────────────
  const { data: exhibitions } = await api('GET', '/api/v1/exhibitions', undefined, supplierToken);
  if (!Array.isArray(exhibitions) || exhibitions.length === 0) {
    await api(
      'POST',
      '/api/v1/exhibitions',
      {
        name: 'Hannover Messe 2026',
        location: 'Hannover, Germany',
        start_date: '2026-04-22',
        end_date: '2026-04-26',
        booth_number: 'Hall 5 B20',
        description: 'Showcasing aerospace & automotive CNC capabilities',
        icp_criteria: {
          target_industries: ['Aerospace', 'Automotive'],
          target_countries: ['DE', 'FR', 'UK'],
        },
      },
      supplierToken,
    );
    console.log('[seed] Exhibition created');
  }

  console.log('[seed] Global setup complete ✔');
}
