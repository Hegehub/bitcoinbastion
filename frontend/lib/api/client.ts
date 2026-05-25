import type { ResponseEnvelope } from '@/types/public-api';

const API_TIMEOUT_MS = 6000;

export class ApiClientError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? '').replace(/\/$/, '');
}

function userSafeMessage(status?: number): string {
  if (status === 404) return 'Requested resource was not found.';
  if (status === 429) return 'Too many requests. Please try again shortly.';
  if (status && status >= 400 && status < 500) return 'Unable to process this request right now.';
  return 'Service is temporarily unavailable. Please retry shortly.';
}

async function parseJsonSafe(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function fetchJson<T>(
  path: string,
  options?: RequestInit,
  fallbackData?: T,
): Promise<T> {
  const base = getApiBaseUrl();
  if (!base && fallbackData !== undefined) return fallbackData;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  try {
    const response = await fetch(`${base}${path}`, {
      ...options,
      method: options?.method ?? 'GET',
      headers: {
        Accept: 'application/json',
        ...(options?.headers ?? {}),
      },
      signal: controller.signal,
      cache: 'no-store',
    });

    const body = await parseJsonSafe(response);

    if (!response.ok) {
      throw new ApiClientError(`http_${response.status}`, userSafeMessage(response.status), response.status);
    }

    return body as T;
  } catch (error) {
    if (fallbackData !== undefined) return fallbackData;
    if (error instanceof ApiClientError) throw error;
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiClientError('timeout', 'Request timed out. Please retry.');
    }
    throw new ApiClientError('unknown', 'Service is temporarily unavailable. Please retry shortly.');
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchEnvelope<T>(path: string, fallbackData?: T): Promise<T> {
  const body = await fetchJson<ResponseEnvelope<T>>(path, undefined, fallbackData ? { success: true, data: fallbackData } : undefined);
  return body.data;
}
