export interface BastionErrorOptions {
  message: string;
  statusCode?: number;
  requestId?: string;
  code?: string;
  details?: unknown;
}

export class BastionApiError extends Error {
  readonly statusCode?: number;
  readonly requestId?: string;
  readonly code?: string;
  readonly details?: unknown;

  constructor(options: BastionErrorOptions) {
    super(options.message);
    this.name = new.target.name;
    this.statusCode = options.statusCode;
    this.requestId = options.requestId;
    this.code = options.code;
    this.details = options.details;
  }
}

export class BastionValidationError extends BastionApiError {}
export class BastionTimeoutError extends BastionApiError {}
export class BastionAuthenticationError extends BastionApiError {}
export class BastionRateLimitError extends BastionApiError {}
export class BastionNotFoundError extends BastionApiError {}
export class BastionServiceUnavailableError extends BastionApiError {}
export class BastionSafetyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BastionSafetyError";
  }
}

export function errorFromStatus(statusCode: number, message: string, details?: unknown, requestId?: string): BastionApiError {
  const options = { message, statusCode, details, requestId };
  if (statusCode === 400 || statusCode === 422) return new BastionValidationError(options);
  if (statusCode === 401 || statusCode === 403) return new BastionAuthenticationError(options);
  if (statusCode === 404) return new BastionNotFoundError(options);
  if (statusCode === 429) return new BastionRateLimitError(options);
  if (statusCode >= 500) return new BastionServiceUnavailableError(options);
  return new BastionApiError(options);
}
