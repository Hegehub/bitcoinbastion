import type { BastionHttpClient } from "../http.js";
import { assertNoSensitiveMaterial } from "../safety.js";

export class TreasuryResource {
  constructor(private readonly http: BastionHttpClient) {}
  createRequest(payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post("/treasury/requests", payload, { requireAuth: true }); }
  listRequests(options: { limit?: number; offset?: number; status?: string } = {}): Promise<unknown> { return this.http.get("/treasury/requests", { query: options, requireAuth: true }); }
  pendingApprovals(options: { limit?: number; offset?: number } = {}): Promise<unknown> { return this.http.get("/treasury/requests/pending-approvals", { query: options, requireAuth: true }); }
  approveRequest(requestId: string | number, payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post(`/treasury/requests/${requestId}/approve`, payload, { requireAuth: true }); }
  rejectRequest(requestId: string | number, payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post(`/treasury/requests/${requestId}/reject`, payload, { requireAuth: true }); }
}
