export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

export type ApiResult<T> = {
  data: T;
  source: 'api' | 'mock';
};

const DEFAULT_TIMEOUT_MS = 5000;

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
      ...init,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    const payload = (await response.json()) as T | { data: T };
    return (payload as { data?: T }).data ?? (payload as T);
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function requestWithFallback<T>(path: string, fallback: T, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    const data = await request<T>(path, init);
    return { data, source: 'api' };
  } catch (error) {
    if (process.env.NODE_ENV !== 'production') {
      // eslint-disable-next-line no-console
      console.warn(`EQIP API unavailable for ${path}; using mock data.`, error);
    }

    return { data: fallback, source: 'mock' };
  }
}
