import type { BastionHttpClient } from "../http.js";

export interface SignalListOptions { limit?: number; offset?: number; horizon?: string }

export class SignalsResource {
  constructor(private readonly http: BastionHttpClient) {}
  listTop(options: SignalListOptions = {}): Promise<unknown> { return this.http.get("/signals/top", { query: { ...options } }); }
  latest(options: { limit?: number } = {}): Promise<unknown> { return this.http.get("/signals/latest", { query: options }); }
  get(signalId: string | number): Promise<unknown> { return this.http.get(`/signals/${signalId}`); }
  getEvidence(signalId: string | number): Promise<unknown> { return this.http.get(`/signals/${signalId}/evidence`); }
  getDeliveryLogs(signalId: string | number): Promise<unknown> { return this.http.get(`/signals/${signalId}/delivery-logs`); }
  getExplanation(signalId: string | number): Promise<unknown> { return this.http.get(`/signals/${signalId}/explanation`); }
  getRecommendations(signalId: string | number): Promise<unknown> { return this.http.get(`/signals/${signalId}/recommendations`); }
}
