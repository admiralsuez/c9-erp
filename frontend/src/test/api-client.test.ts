/**
 * Phase 3.1 test suite: single-flight token refresh.
 *
 * ``refreshAccessToken`` (exported from the client) must:
 *   1. issue only ONE ``/auth/refresh`` POST even when many callers invoke it
 *      concurrently in the same tick;
 *   2. persist the returned access token to localStorage;
 *   3. reset its pending promise after settling (so a later call refreshes again).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Capture the axios post mock via hoisted module mock.
const mocks = vi.hoisted(() => {
  return {
    post: vi.fn(),
  };
});

vi.mock('axios', () => {
  return {
    default: {
      post: mocks.post,
      create: () => ({
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
      }),
    },
  };
});

import { refreshAccessToken, __resetPendingRefreshForTests } from '../api/client';

// Control when the (single) refresh promise settles.
let resolveRefresh: ((token: string) => void) | undefined;

function armRefresh(_token = 'new-token-xyz') {
  mocks.post.mockImplementation(
    () =>
      new Promise<{ data: { access_token: string } }>((resolve) => {
        resolveRefresh = (t: string) => resolve({ data: { access_token: t } });
      }),
  );
}

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem('refresh_token', 'test-refresh');
  mocks.post.mockReset();
  __resetPendingRefreshForTests();
});

afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe('single-flight token refresh', () => {
  it('issues exactly one /auth/refresh for N concurrent callers', async () => {
    armRefresh();

    // Kick off N concurrent refreshes before any settles.
    const p1 = refreshAccessToken();
    const p2 = refreshAccessToken();
    const p3 = refreshAccessToken();

    resolveRefresh?.('shared-token');

    const results = await Promise.all([p1, p2, p3]);
    expect(results).toEqual(['shared-token', 'shared-token', 'shared-token']);

    // Only one network call went out.
    const refreshCalls = mocks.post.mock.calls.filter((c) =>
      String(c[0]).endsWith('/auth/refresh'),
    );
    expect(refreshCalls).toHaveLength(1);
  });

  it('persists the new access token to localStorage', async () => {
    armRefresh('fresh-token-42');
    const p = refreshAccessToken();
    resolveRefresh?.('fresh-token-42');
    await p;

    expect(localStorage.getItem('access_token')).toBe('fresh-token-42');
  });

  it('resets pending state so a later call refreshes again', async () => {
    armRefresh('first-token');
    const first = refreshAccessToken();
    resolveRefresh?.('first-token');
    await first;

    // A second, distinct refresh should trigger a brand-new POST because the
    // previous pending promise was reset by ``.finally``.
    mocks.post.mockReset();
    armRefresh('second-token');
    const second = refreshAccessToken();
    resolveRefresh?.('second-token');
    const token = await second;

    expect(token).toBe('second-token');
    const refreshCalls = mocks.post.mock.calls.filter((c) =>
      String(c[0]).endsWith('/auth/refresh'),
    );
    expect(refreshCalls).toHaveLength(1);
  });

  it('rejects when no refresh token is available', async () => {
    localStorage.removeItem('refresh_token');
    await expect(refreshAccessToken()).rejects.toThrow('No refresh token available');
  });
});