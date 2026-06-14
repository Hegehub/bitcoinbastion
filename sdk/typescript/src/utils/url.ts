export function trimSlashes(value: string): string {
  return value.replace(/^\/+|\/+$/g, "");
}

export function joinUrl(baseUrl: string, apiPrefix: string, path: string): string {
  const base = baseUrl.replace(/\/+$/g, "");
  const prefix = trimSlashes(apiPrefix);
  const normalizedPath = trimSlashes(path);
  return `${base}/${prefix}/${normalizedPath}`;
}

export function withQuery(url: string, query?: Record<string, unknown>): string {
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}
