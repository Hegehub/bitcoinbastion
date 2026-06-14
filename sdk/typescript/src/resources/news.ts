import type { BastionHttpClient } from "../http.js";

export class NewsResource {
  constructor(private readonly http: BastionHttpClient) {}
  latest(options: { limit?: number; offset?: number } = {}): Promise<unknown> { return this.http.get("/news/latest", { query: options }); }
  events(options: { limit?: number; offset?: number } = {}): Promise<unknown> { return this.http.get("/news/events", { query: options }); }
  getArticle(articleId: string | number): Promise<unknown> { return this.http.get(`/news/articles/${articleId}`); }
  getEvent(eventId: string | number): Promise<unknown> { return this.http.get(`/news/events/${eventId}`); }
}
