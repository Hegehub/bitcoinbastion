export interface ResponseEnvelope<T> {
  data?: T;
  error?: unknown;
  meta?: Record<string, unknown>;
}

export interface PaginatedData<T> {
  items: T[];
  total?: number;
  limit?: number;
  offset?: number;
}

export interface RequestOptions {
  raw?: boolean;
  signal?: AbortSignal;
}

export type JsonObject = Record<string, unknown>;
