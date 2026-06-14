export function assertNonEmptyString(value: string, name: string): void {
  if (!value.trim()) throw new Error(`${name} must be non-empty`);
}
