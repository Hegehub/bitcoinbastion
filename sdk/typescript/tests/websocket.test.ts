import { describe, expect, it } from "vitest";
import { BitcoinBastionClient } from "../src/index.js";

describe("websocket", () => {
  it("builds generic event URL with topics", () => {
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000" });
    const url = client.websocket.buildUrl("/ws/events", { topics: "signals,trace" });
    expect(url).toBe("ws://localhost:8000/api/v1/ws/events?topics=signals%2Ctrace");
  });

  it("opens specialized stream with injected WebSocket", () => {
    const opened: string[] = [];
    class FakeWebSocket {
      onopen: (() => void) | null = null;
      onclose: (() => void) | null = null;
      onerror: ((event: unknown) => void) | null = null;
      onmessage: ((event: { data: string }) => void) | null = null;
      constructor(url: string) { opened.push(url); }
      close(): void { this.onclose?.(); }
    }
    const client = new BitcoinBastionClient({ baseUrl: "http://localhost:8000", WebSocketImpl: FakeWebSocket as unknown as typeof WebSocket });
    const sub = client.websocket.signals({ onEvent: () => undefined, onError: () => undefined });
    sub.close();
    expect(opened[0]).toBe("ws://localhost:8000/api/v1/ws/signals");
  });
});
