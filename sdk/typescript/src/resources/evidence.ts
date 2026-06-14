import type { BastionHttpClient } from "../http.js";

export class EvidenceResource {
  constructor(private readonly http: BastionHttpClient) {}
  getPacket(packetId: string | number): Promise<unknown> { return this.http.get(`/evidence/packets/${packetId}`); }
  getReplay(packetId: string | number): Promise<unknown> { return this.http.get(`/evidence/replay/packet/${packetId}`); }
  exportJson(packetId: string | number): Promise<unknown> { return this.http.get(`/evidence/packets/${packetId}`, { query: { format: "json" } }); }
  exportMarkdown(packetId: string | number): Promise<unknown> { return this.http.get(`/evidence/packets/${packetId}`, { query: { format: "markdown" } }); }
}
