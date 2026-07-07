import type { BastionAccessAuthConfig } from "./auth.js";

export interface BitcoinBastionClientConfig {
  baseUrl: string;
  /** @deprecated Legacy bearer/api-key auth is disabled by default; use accessAuth. */
  apiKey?: string;
  /** @deprecated Legacy bearer auth is hard-disabled; this compatibility field still fails closed. */
  bearerToken?: string;
  timeoutMs?: number;
  apiPrefix?: string;
  headers?: Record<string, string>;
  fetchImpl?: typeof fetch;
  WebSocketImpl?: typeof WebSocket;
  accessAuth?: BastionAccessAuthConfig;
  allowLegacyBearerAuth?: boolean;
  redactSensitiveLogs?: boolean;
}

export interface NormalizedConfig extends Required<Pick<BitcoinBastionClientConfig, "baseUrl" | "timeoutMs" | "apiPrefix">> {
  apiKey?: string;
  headers: Record<string, string>;
  fetchImpl: typeof fetch;
  WebSocketImpl?: typeof WebSocket;
  accessAuth?: BastionAccessAuthConfig;
  allowLegacyBearerAuth: boolean;
  redactSensitiveLogs: boolean;
}

export function normalizeConfig(config: BitcoinBastionClientConfig): NormalizedConfig {
  return {
    baseUrl: config.baseUrl.replace(/\/+$/g, ""),
    apiKey: config.apiKey ?? config.bearerToken,
    timeoutMs: config.timeoutMs ?? 5000,
    apiPrefix: config.apiPrefix ?? "/api/v1",
    headers: config.headers ?? {},
    fetchImpl: config.fetchImpl ?? fetch,
    WebSocketImpl: config.WebSocketImpl,
    accessAuth: config.accessAuth,
    allowLegacyBearerAuth: config.allowLegacyBearerAuth ?? false,
    redactSensitiveLogs: config.redactSensitiveLogs ?? true,
  };
}
