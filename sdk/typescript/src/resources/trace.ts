import type { BastionHttpClient } from "../http.js";
import { assertNoSensitiveMaterial } from "../safety.js";

export class TraceResource {
  constructor(private readonly http: BastionHttpClient) {}
  analyzeAddress(address: string): Promise<unknown> { assertNoSensitiveMaterial(address); return this.http.get(`/trace/address/${address}`); }
  getLite(address: string): Promise<unknown> { assertNoSensitiveMaterial(address); return this.http.get(`/trace/lite/${address}`); }
  getReport(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}`); }
  getPublicSummary(reportId: string | number): Promise<unknown> { return this.http.get(`/public/trace/${reportId}/summary`); }
  getEvidence(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}/evidence`); }
  getPrivacyShield(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}/privacy-shield`); }
  getOriginPassport(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}/origin-passport`); }
  getProviderDisagreement(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}/provider-disagreement`); }
  getCounterpartyLens(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}/counterparty-lens`); }
  getPolicyFacts(reportId: string | number): Promise<unknown> { return this.http.get(`/trace/report/${reportId}/policy-facts`); }
  batch(addresses: string[]): Promise<unknown> { assertNoSensitiveMaterial(addresses); return this.http.post("/trace/business/batch", { addresses }); }
}
