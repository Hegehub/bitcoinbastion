import type { BastionHttpClient } from "../http.js";

export class ProviderHealthResource {
  constructor(private readonly http: BastionHttpClient) {}
  status(): Promise<unknown> { return this.http.get("/health/runtime"); }
  providers(): Promise<unknown> { return this.http.get("/health/providers"); }
  degraded(): Promise<unknown> { return this.http.get("/health/degraded"); }
}
