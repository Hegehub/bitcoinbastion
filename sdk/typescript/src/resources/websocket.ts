import type { NormalizedConfig } from "../config.js";
import type { BastionEventEnvelope } from "../schemas/events.js";

export interface SubscribeOptions {
  topics?: string[];
  onEvent(event: BastionEventEnvelope | Record<string, unknown>): void;
  onError(error: unknown): void;
  onOpen?(): void;
  onClose?(): void;
}

export interface Subscription { close(): void }

export class WebSocketResource {
  constructor(private readonly config: NormalizedConfig) {}

  subscribe(options: SubscribeOptions): Subscription {
    return this.open("/ws/events", options, options.topics ? { topics: options.topics.join(",") } : undefined);
  }
  signals(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/signals", options); }
  trace(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/trace", options); }
  market(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/market", options); }
  news(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/news", options); }
  onchain(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/onchain", options); }
  treasury(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/treasury", options); }
  providerHealth(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/provider-health", options); }
  intelligenceTimeline(options: Omit<SubscribeOptions, "topics">): Subscription { return this.open("/ws/intelligence-timeline", options); }

  buildUrl(path: string, query?: Record<string, string>): string {
    const httpUrl = new URL(`${this.config.baseUrl}${this.config.apiPrefix}${path}`);
    httpUrl.protocol = httpUrl.protocol === "https:" ? "wss:" : "ws:";
    if (query) for (const [key, value] of Object.entries(query)) httpUrl.searchParams.set(key, value);
    return httpUrl.toString();
  }

  private open(path: string, options: Omit<SubscribeOptions, "topics">, query?: Record<string, string>): Subscription {
    const WebSocketImpl = this.config.WebSocketImpl ?? globalThis.WebSocket;
    if (!WebSocketImpl) throw new Error("WebSocket implementation is not available; provide WebSocketImpl in client config.");
    const ws = new WebSocketImpl(this.buildUrl(path, query));
    ws.onopen = () => options.onOpen?.();
    ws.onclose = () => options.onClose?.();
    ws.onerror = (event) => options.onError(event);
    ws.onmessage = (event) => {
      try {
        options.onEvent(JSON.parse(String(event.data)) as BastionEventEnvelope | Record<string, unknown>);
      } catch (error) {
        options.onError(error);
      }
    };
    return { close: () => ws.close() };
  }
}
