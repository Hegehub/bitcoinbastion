import type { BastionHttpClient } from "../http.js";
import { assertNoSensitiveMaterial } from "../safety.js";

export class PolicyResource {
  constructor(private readonly http: BastionHttpClient) {}
  evaluate(payload: unknown): Promise<unknown> { assertNoSensitiveMaterial(payload); return this.http.post("/policy/check", payload); }
  profiles(): Promise<unknown> { return this.http.get("/policy/catalog"); }
  getProfile(profileId: string): Promise<unknown> { return this.http.get(`/policy/catalog/${profileId}`); }
}
