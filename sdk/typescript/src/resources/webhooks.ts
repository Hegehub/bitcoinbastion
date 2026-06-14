import type { BastionHttpClient } from "../http.js";

export interface CreateWebhookPayload {
  url: string;
  events: string[];
  description?: string;
  enabled?: boolean;
}

export class WebhooksResource {
  constructor(private readonly http: BastionHttpClient) {}
  create(payload: CreateWebhookPayload): Promise<unknown> {
    return this.http.post("/webhooks", { target_url: payload.url, event_types: payload.events, description: payload.description, enabled: payload.enabled, name: payload.url });
  }
  list(): Promise<unknown> { return this.http.get("/webhooks"); }
  get(webhookId: string | number): Promise<unknown> { return this.http.get(`/webhooks/${webhookId}`); }
  update(webhookId: string | number, payload: unknown): Promise<unknown> { return this.http.patch(`/webhooks/${webhookId}`, payload); }
  delete(webhookId: string | number): Promise<unknown> { return this.http.delete(`/webhooks/${webhookId}`); }
  test(webhookId: string | number): Promise<unknown> { return this.http.post(`/webhooks/${webhookId}/test`, {}); }
  deliveries(webhookId: string | number): Promise<unknown> { return this.http.get(`/webhooks/${webhookId}/deliveries`); }
}
