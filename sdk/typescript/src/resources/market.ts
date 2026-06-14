import type { BastionHttpClient } from "../http.js";

export class MarketResource {
  constructor(private readonly http: BastionHttpClient) {}
  dashboard(options: { timeframe?: string } = {}): Promise<unknown> { return this.http.get("/market/btc/context", { query: options }); }
  timeline(options: { filter?: string; page?: number; pageSize?: number; sort?: "asc" | "desc"; window?: string } = {}): Promise<unknown> { return this.http.get("/intelligence/timeline/latest", { query: options }); }
  candle(candleId: string | number): Promise<unknown> { return this.http.get(`/intelligence/candles/${candleId}`); }
  evidence(packetId: string | number): Promise<unknown> { return this.http.get(`/evidence/packets/${packetId}`); }
  timeMachine(options: { timeframe?: string } = {}): Promise<unknown> { return this.http.get("/market/btc/context", { query: options }); }
}
