import { BastionAccessAuth, authHeaders } from "./auth.js";
import type { NormalizedConfig } from "./config.js";
import { AccessAuthRequiredError, BastionTimeoutError, errorFromStatus } from "./errors.js";
import type { ResponseEnvelope } from "./schemas/common.js";
import { joinUrl, withQuery } from "./utils/url.js";

export interface HttpRequestOptions {
  query?: Record<string, unknown>;
  body?: unknown;
  raw?: boolean;
  signal?: AbortSignal;
  requireAuth?: boolean;
}

export class BastionHttpClient {
  private readonly accessAuth?: BastionAccessAuth;

  constructor(private readonly config: NormalizedConfig) {
    this.accessAuth = config.accessAuth ? new BastionAccessAuth(config.accessAuth) : undefined;
  }

  async get<T = unknown>(path: string, options: HttpRequestOptions = {}): Promise<T> {
    return this.request<T>("GET", path, options);
  }

  async post<T = unknown>(path: string, body?: unknown, options: HttpRequestOptions = {}): Promise<T> {
    return this.request<T>("POST", path, { ...options, body });
  }

  async patch<T = unknown>(path: string, body?: unknown, options: HttpRequestOptions = {}): Promise<T> {
    return this.request<T>("PATCH", path, { ...options, body });
  }

  async delete<T = unknown>(path: string, options: HttpRequestOptions = {}): Promise<T> {
    return this.request<T>("DELETE", path, options);
  }

  getAccessAuth(): BastionAccessAuth | undefined {
    return this.accessAuth;
  }

  private async request<T>(method: string, path: string, options: HttpRequestOptions): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);
    const signal = options.signal ?? controller.signal;
    const url = withQuery(joinUrl(this.config.baseUrl, this.config.apiPrefix, path), options.query);
    const signingPath = new URL(url).pathname + new URL(url).search;
    try {
      const accessHeaders = await this.accessHeaders(method, signingPath, options.body, Boolean(options.requireAuth));
      const response = await this.config.fetchImpl(url, {
        method,
        signal,
        headers: {
          "content-type": "application/json",
          ...this.config.headers,
          ...authHeaders(this.config.apiKey, {
            allowLegacyBearerAuth: this.config.allowLegacyBearerAuth,
          }),
          ...accessHeaders,
        },
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
      });
      const requestId = response.headers.get("x-request-id") ?? undefined;
      const payload = await parseJson(response);
      if (!response.ok) throw errorFromStatus(response.status, safeMessage(response.status), payload, requestId);
      return (options.raw ? payload : unwrapEnvelope(payload)) as T;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new BastionTimeoutError({ message: "Bitcoin Bastion request timed out." });
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  private async accessHeaders(method: string, path: string, body: unknown, requireAuth: boolean): Promise<Record<string, string>> {
    if (!this.accessAuth) {
      if (requireAuth) throw new AccessAuthRequiredError();
      return {};
    }
    if (!requireAuth && !this.accessAuth.getSession()) return {};
    return this.accessAuth.signRequest(method, path, body);
  }
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  return JSON.parse(text) as unknown;
}

function unwrapEnvelope(payload: unknown): unknown {
  if (payload && typeof payload === "object" && "data" in payload) {
    const envelope = payload as ResponseEnvelope<unknown>;
    if (envelope.error) throw errorFromStatus(500, "Bitcoin Bastion returned an error envelope.", envelope.error);
    return envelope.data;
  }
  return payload;
}

function safeMessage(status: number): string {
  if (status === 400 || status === 422) return "Invalid Bitcoin Bastion request.";
  if (status === 401 || status === 403) return "Bitcoin Bastion authentication failed.";
  if (status === 404) return "Bitcoin Bastion resource was not found.";
  if (status === 429) return "Bitcoin Bastion rate limit exceeded.";
  return "Bitcoin Bastion service unavailable.";
}
