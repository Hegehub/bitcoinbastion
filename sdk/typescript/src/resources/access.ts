import type { BastionAccessChallengeResponse, BastionAccessSession } from "../auth.js";
import type { BastionHttpClient } from "../http.js";
import { assertNoSensitiveMaterial } from "../safety.js";

export class AccessResource {
  constructor(private readonly http: BastionHttpClient) {}

  createChallenge(payload: Record<string, unknown>): Promise<BastionAccessChallengeResponse> {
    assertNoSensitiveMaterial(payload);
    return this.http.post("/access/challenges", payload);
  }

  createSession(payload: Record<string, unknown>): Promise<BastionAccessSession> {
    assertNoSensitiveMaterial(payload);
    return this.http.post("/access/sessions", payload);
  }

  me(): Promise<unknown> {
    return this.http.get("/access/me", { requireAuth: true });
  }

  entitlements(): Promise<unknown> {
    return this.http.get("/access/me/entitlements", { requireAuth: true });
  }

  limits(): Promise<unknown> {
    return this.http.get("/access/me/limits", { requireAuth: true });
  }
}
