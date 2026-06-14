export interface BitcoinBastionClientConfig {
  baseUrl: string;
  apiKey?: string;
  timeoutMs?: number;
  apiPrefix?: string;
  headers?: Record<string, string>;
  fetchImpl?: typeof fetch;
  WebSocketImpl?: typeof WebSocket;
}

export interface NormalizedConfig extends Required<Pick<BitcoinBastionClientConfig, "baseUrl" | "timeoutMs" | "apiPrefix">> {
  apiKey?: string;
  headers: Record<string, string>;
  fetchImpl: typeof fetch;
  WebSocketImpl?: typeof WebSocket;
}

export function normalizeConfig(config: BitcoinBastionClientConfig): NormalizedConfig {
  return {
    baseUrl: config.baseUrl.replace(/\/+$/g, ""),
    apiKey: config.apiKey,
    timeoutMs: config.timeoutMs ?? 5000,
    apiPrefix: config.apiPrefix ?? "/api/v1",
    headers: config.headers ?? {},
    fetchImpl: config.fetchImpl ?? fetch,
    WebSocketImpl: config.WebSocketImpl,
  };
}
