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
export class BastionAuthError extends BastionApiError {}
export class BastionSessionExpiredError extends Error { constructor(message = "PoP Session is expired.") { super(message); this.name = new.target.name; } }
export class BastionStepUpRequiredError extends BastionApiError {}
export class BastionUpgradeRequiredError extends BastionApiError {}
export class BastionQuotaExceededError extends BastionApiError {}
export class BastionMetricNotAllowedError extends BastionApiError {}
export class BastionPrincipalRevokedError extends BastionApiError {}
export class BastionRecoveryRequiredError extends BastionApiError {}
export class BastionLnurlError extends BastionApiError {}
export class BastionLnurlDomainMismatchError extends BastionLnurlError {}
export class BastionPaymentNotSettledError extends BastionLnurlError {}
export class BastionWithdrawPolicyError extends BastionLnurlError {}
export class BastionSafetyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BastionSafetyError";
  }
}

export class AccessAuthRequiredError extends Error {
  constructor(message = "Proof-of-Access session is required for this protected SDK request.") {
    super(message);
    this.name = "AccessAuthRequiredError";
  }
}

export class AccessSessionExpiredError extends Error {
  constructor(message = "Proof-of-Access session is expired.") {
    super(message);
    this.name = "AccessSessionExpiredError";
  }
}

export class AccessSigningError extends Error {
  constructor(message = "Proof-of-Access request signing failed.") {
    super(message);
    this.name = "AccessSigningError";
  }
}

export class AccessChallengeError extends Error {
  constructor(message = "Proof-of-Access challenge failed.") {
    super(message);
    this.name = "AccessChallengeError";
  }
}

export class AccessLegacyAuthDisabledError extends Error {
  constructor(message = "Legacy bearer auth is disabled. Use Proof-of-Access challenge/session flow.") {
    super(message);
    this.name = "AccessLegacyAuthDisabledError";
  }
}

export class AccessSensitiveMaterialError extends Error {
  constructor(message = "Sensitive Access material was rejected.") {
    super(message);
    this.name = "AccessSensitiveMaterialError";
  }
}

function errorCode(details: unknown): string | undefined {
  if (!details || typeof details !== "object") return undefined;
  const payload = details as Record<string, unknown>;
  const error = payload.error;
  if (error && typeof error === "object" && typeof (error as Record<string, unknown>).code === "string") {
    return (error as Record<string, string>).code;
  }
  return typeof payload.code === "string" ? payload.code : undefined;
}

export function errorFromStatus(
  statusCode: number,
  message: string,
  details?: unknown,
  requestId?: string,
): BastionApiError | Error {
  const code = errorCode(details);
  const policy = { message, statusCode, details, requestId, code };
  if (code === "step_up_required") return new BastionStepUpRequiredError(policy);
  if (code === "upgrade_required") return new BastionUpgradeRequiredError(policy);
  if (code === "quota_exceeded") return new BastionQuotaExceededError(policy);
  if (code === "metric_not_allowed") return new BastionMetricNotAllowedError(policy);
  if (code === "principal_revoked" || code === "revoked") return new BastionPrincipalRevokedError(policy);
  if (code === "recovery_required") return new BastionRecoveryRequiredError(policy);
  if (code === "lnurl_domain_mismatch") return new BastionLnurlDomainMismatchError(policy);
  if (code === "access_session_expired" || code === "session_expired") return new AccessSessionExpiredError();
  if (code === "access_signature_required" || code === "access_signature_invalid" || code === "invalid_signature") return new AccessSigningError();
  if (code === "challenge_expired") return new AccessChallengeError("Proof-of-Access challenge is expired.");
  const options = { message, statusCode, details, requestId, code };
  if (statusCode === 400 || statusCode === 422) return new BastionValidationError(options);
  if (statusCode === 401 || statusCode === 403) return new BastionAuthenticationError(options);
  if (statusCode === 404) return new BastionNotFoundError(options);
  if (statusCode === 429) return new BastionRateLimitError(options);
  if (statusCode >= 500) return new BastionServiceUnavailableError(options);
  return new BastionApiError(options);
}
