export function exponentialBackoffMs(attempt: number, initialMs = 500, maxMs = 10_000): number {
  return Math.min(maxMs, initialMs * 2 ** Math.max(0, attempt - 1));
}
