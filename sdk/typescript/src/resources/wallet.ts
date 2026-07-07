import type { BastionHttpClient } from "../http.js";
import { assertNoSensitiveMaterial } from "../safety.js";

export class WalletResource {
  constructor(private readonly http: BastionHttpClient) {}
  health(walletId: string | number): Promise<unknown> { assertNoSensitiveMaterial(walletId); return this.http.get(`/wallet/profiles/${walletId}/health/reports`, { query: { limit: 1 }, requireAuth: true }); }
  privacyRisk(walletId: string | number): Promise<unknown> { assertNoSensitiveMaterial(walletId); return this.http.get(`/wallet/profiles/${walletId}/health/reports`, { query: { limit: 1 }, requireAuth: true }); }
}
