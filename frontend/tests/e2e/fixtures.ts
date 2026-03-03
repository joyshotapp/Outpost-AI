/**
 * Factory Insider — Shared Playwright fixtures
 *
 * Provides:
 *   1. `apiLogin(email, password)` → JWT token via real backend
 *   2. `seedSupplierToken` / `seedBuyerToken` — pre-authenticated contexts
 *   3. `api` — helper for raw backend REST calls
 */
import { test as base, expect, type Page } from '@playwright/test';

/* ──────────── Constants ────────────────────────────────────────────────── */
export const BACKEND = 'http://localhost:8001';

export const SUPPLIER = {
  email: 'test@factory.com',
  password: 'Test1234!',
  tokenKey: 'auth_token',   // the key supplier login page writes to localStorage
};

export const BUYER = {
  email: 'buyer@aerospace.de',
  password: 'Buyer5678!',
  tokenKey: 'auth_token',
};

/* ──────────── API helpers ──────────────────────────────────────────────── */

/** Login via backend REST and return JWT token string */
export async function apiLogin(email: string, password: string): Promise<string> {
  const res = await fetch(`${BACKEND}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(`Login failed for ${email}: ${res.status}`);
  const data = await res.json();
  return data.access_token;
}

/** Inject JWT into the browser localStorage so the app auto-authenticates */
export async function injectAuth(page: Page, token: string, storageKey = 'auth_token') {
  await page.addInitScript(
    ({ key, value }: { key: string; value: string }) => {
      window.localStorage.setItem(key, value);
      // Some pages read "access_token" or "token" — mirror to all keys
      window.localStorage.setItem('access_token', value);
      window.localStorage.setItem('token', value);
    },
    { key: storageKey, value: token },
  );
}

/** Generic REST helper (returns parsed JSON) */
export async function api(
  method: string,
  path: string,
  token?: string,
  body?: unknown,
) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BACKEND}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${method} ${path} → ${res.status}: ${text}`);
  }
  return res.json();
}

/* ──────────── Extended test fixture ───────────────────────────────────── */

type Fixtures = {
  supplierToken: string;
  buyerToken: string;
  authedSupplierPage: Page;
  authedAdminPage: Page;
  authedBuyerPage: Page;
};

export const test = base.extend<Fixtures>({
  supplierToken: async ({}, use) => {
    const token = await apiLogin(SUPPLIER.email, SUPPLIER.password);
    await use(token);
  },
  buyerToken: async ({}, use) => {
    const token = await apiLogin(BUYER.email, BUYER.password);
    await use(token);
  },
  authedSupplierPage: async ({ page, supplierToken }, use) => {
    await injectAuth(page, supplierToken);
    await use(page);
  },
  authedAdminPage: async ({ page, supplierToken }, use) => {
    // Admin uses the same supplier user (role check is on backend side)
    await injectAuth(page, supplierToken);
    await use(page);
  },
  authedBuyerPage: async ({ page, buyerToken }, use) => {
    await injectAuth(page, buyerToken);
    await use(page);
  },
});

export { expect };
