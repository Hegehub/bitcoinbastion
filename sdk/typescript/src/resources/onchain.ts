import type { BastionHttpClient } from "../http.js";

export class OnchainResource {
  constructor(private readonly http: BastionHttpClient) {}
  events(options: { limit?: number; offset?: number } = {}): Promise<unknown> { return this.http.get("/onchain/events", { query: options }); }
  state(options: { providerProbe?: boolean } = {}): Promise<unknown> { return this.http.get("/onchain/state", { query: options }); }
}
