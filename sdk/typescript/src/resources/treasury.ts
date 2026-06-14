import type { BastionHttpClient } from "../http.js";
import { assertNoSensitiveMaterial } from "../safety.js";

export class TreasuryResource {
  constructor(private readonly http: BastionHttpClient) {}
  createRequest(payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post("/treasury/requests", payload); }
  listRequests(options: { limit?: number; offset?: number; status?: string } = {}): Promise<unknown> { return this.http.get("/treasury/requests", { query: options }); }
  pendingApprovals(options: { limit?: number; offset?: number } = {}): Promise<unknown> { return this.http.get("/treasury/requests/pending-approvals", { query: options }); }
  approveRequest(requestId: string | number, payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post(`/treasury/requests/${requestId}/approve`, payload); }
  rejectRequest(requestId: string | number, payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post(`/treasury/requests/${requestId}/reject`, payload); }
}
