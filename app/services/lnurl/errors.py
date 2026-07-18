"""Safe typed errors for LNURL encoding and URL safety."""


class LNURLError(ValueError):
    code = "lnurl_error"
    default_message = "LNURL value is invalid."

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        self.code = code or self.code
        super().__init__(message or self.default_message)


class LNURLEncodingError(LNURLError):
    code = "lnurl_encoding_error"
    default_message = "LNURL could not be encoded."


class LNURLDecodingError(LNURLError):
    code = "lnurl_decoding_error"
    default_message = "LNURL could not be decoded."


class LNURLInvalidChecksumError(LNURLDecodingError):
    code = "lnurl_invalid_checksum"
    default_message = "LNURL checksum is invalid."


class LNURLInvalidHRPError(LNURLDecodingError):
    code = "lnurl_invalid_hrp"
    default_message = "LNURL human-readable prefix is invalid."


class LNURLMixedCaseError(LNURLDecodingError):
    code = "lnurl_mixed_case"
    default_message = "LNURL mixed case is not allowed."


class LNURLInvalidUTF8Error(LNURLDecodingError):
    code = "lnurl_invalid_utf8"
    default_message = "Decoded LNURL is not valid UTF-8."


class LNURLInputTooLargeError(LNURLError):
    code = "lnurl_input_too_large"
    default_message = "LNURL input exceeds configured size limits."


class LNURLUnsafeURLError(LNURLError):
    code = "lnurl_unsafe_url"
    default_message = "LNURL URL is not safe for the requested purpose."


class LNURLUnsupportedSchemeError(LNURLUnsafeURLError):
    code = "lnurl_unsupported_scheme"
    default_message = "URL scheme is not allowed."


class LNURLInvalidHostError(LNURLUnsafeURLError):
    code = "lnurl_invalid_host"
    default_message = "URL host is invalid."


class LNURLCredentialsForbiddenError(LNURLUnsafeURLError):
    code = "lnurl_credentials_forbidden"
    default_message = "URL credentials are forbidden."


class LNURLFragmentForbiddenError(LNURLUnsafeURLError):
    code = "lnurl_fragment_forbidden"
    default_message = "URL fragments are forbidden."


class LNURLPortForbiddenError(LNURLUnsafeURLError):
    code = "lnurl_port_forbidden"
    default_message = "URL port is not allowed."


class LNURLPrivateTargetError(LNURLUnsafeURLError):
    code = "lnurl_private_target"
    default_message = "URL target is private or reserved."


class LNURLLoopbackTargetError(LNURLPrivateTargetError):
    code = "lnurl_loopback_target"
    default_message = "URL target is loopback."


class LNURLLinkLocalTargetError(LNURLPrivateTargetError):
    code = "lnurl_link_local_target"
    default_message = "URL target is link-local."


class LNURLOnionValidationError(LNURLUnsafeURLError):
    code = "lnurl_onion_invalid"
    default_message = "Onion URL is invalid for this policy."


class LNURLAuthDomainMismatchError(LNURLUnsafeURLError):
    code = "lnurl_auth_domain_mismatch"
    default_message = "LNURL-auth domain does not match the stable configured domain."


class LNURLDNSResolutionError(LNURLUnsafeURLError):
    code = "lnurl_dns_resolution_error"
    default_message = "LNURL target DNS resolution failed safely."


class LNURLRedirectForbiddenError(LNURLUnsafeURLError):
    code = "lnurl_redirect_forbidden"
    default_message = "LNURL redirect target is not allowed."


class LNURLK1Error(LNURLError):
    code = "lnurl_k1_error"
    default_message = "LNURL k1 challenge is invalid."


class LNURLK1MalformedError(LNURLK1Error):
    code = "lnurl_k1_malformed"
    default_message = "LNURL k1 challenge is malformed."


class LNURLK1UnknownError(LNURLK1Error):
    code = "lnurl_k1_unknown"
    default_message = "LNURL k1 challenge is unknown or unavailable."


class LNURLK1ExpiredError(LNURLK1Error):
    code = "lnurl_k1_expired"
    default_message = "LNURL k1 challenge is expired."


class LNURLK1ConsumedError(LNURLK1Error):
    code = "lnurl_k1_consumed"
    default_message = "LNURL k1 challenge was already used."


class LNURLK1RevokedError(LNURLK1Error):
    code = "lnurl_k1_revoked"
    default_message = "LNURL k1 challenge is revoked."


class LNURLK1BindingMismatchError(LNURLK1Error):
    code = "lnurl_k1_binding_mismatch"
    default_message = "LNURL k1 challenge binding does not match."


class LNURLK1DomainMismatchError(LNURLK1BindingMismatchError):
    code = "lnurl_k1_domain_mismatch"
    default_message = "LNURL k1 challenge domain does not match."


class LNURLK1ActionMismatchError(LNURLK1BindingMismatchError):
    code = "lnurl_k1_action_mismatch"
    default_message = "LNURL k1 challenge action does not match."


class LNURLK1PolicyMismatchError(LNURLK1BindingMismatchError):
    code = "lnurl_k1_policy_mismatch"
    default_message = "LNURL k1 challenge policy does not match."


class LNURLK1ConcurrencyError(LNURLK1Error):
    code = "lnurl_k1_concurrency_error"
    default_message = "LNURL k1 challenge could not be consumed atomically."


class LNURLK1ConfigurationError(LNURLK1Error):
    code = "lnurl_k1_configuration_error"
    default_message = "LNURL k1 registry is not safely configured."


class LNURLAuthChallengeError(LNURLError):
    code = "lnurl_auth_challenge_error"
    default_message = "LNURL-auth challenge could not be created."


class LNURLAuthConfigurationError(LNURLAuthChallengeError):
    code = "lnurl_auth_configuration_error"
    default_message = "LNURL-auth challenge service is not safely configured."


class LNURLAuthDomainError(LNURLAuthChallengeError):
    code = "lnurl_auth_domain_error"
    default_message = "LNURL-auth domain is not allowed."


class LNURLAuthActionNotAllowedError(LNURLAuthChallengeError):
    code = "lnurl_auth_action_not_allowed"
    default_message = "LNURL-auth action is not allowed."


class LNURLAuthChallengeExpiredError(LNURLAuthChallengeError):
    code = "lnurl_auth_challenge_expired"
    default_message = "LNURL-auth challenge expired."


class LNURLAuthChallengeCancelledError(LNURLAuthChallengeError):
    code = "lnurl_auth_challenge_cancelled"
    default_message = "LNURL-auth challenge cancelled."


class LNURLAuthK1RegistrationError(LNURLAuthChallengeError):
    code = "lnurl_auth_k1_registration_error"
    default_message = "LNURL-auth k1 challenge registration failed."


class LNURLAuthEncodingError(LNURLAuthChallengeError):
    code = "lnurl_auth_encoding_error"
    default_message = "LNURL-auth challenge encoding failed."


class LNURLAuthPolicyPrecheckError(LNURLAuthChallengeError):
    code = "lnurl_auth_policy_precheck_error"
    default_message = "LNURL-auth challenge policy pre-check failed."


class LNURLAuthCallbackError(LNURLError):
    code = "lnurl_auth_callback_error"
    default_message = "LNURL-auth callback could not be verified."


class LNURLAuthMalformedK1Error(LNURLAuthCallbackError):
    code = "lnurl_auth_malformed_k1"
    default_message = "LNURL-auth callback k1 is malformed."


class LNURLAuthUnknownChallengeError(LNURLAuthCallbackError):
    code = "lnurl_auth_unknown_challenge"
    default_message = "LNURL-auth challenge could not be verified."


class LNURLAuthChallengeUsedError(LNURLAuthCallbackError):
    code = "lnurl_auth_challenge_used"
    default_message = "LNURL-auth challenge could not be verified."


class LNURLAuthActionMismatchError(LNURLAuthCallbackError):
    code = "lnurl_auth_action_mismatch"
    default_message = "LNURL-auth action does not match the challenge."


class LNURLAuthInvalidPublicKeyError(LNURLAuthCallbackError):
    code = "lnurl_auth_invalid_public_key"
    default_message = "LNURL-auth public key is invalid."


class LNURLAuthMalformedSignatureError(LNURLAuthCallbackError):
    code = "lnurl_auth_malformed_signature"
    default_message = "LNURL-auth signature is malformed."


class LNURLAuthInvalidSignatureError(LNURLAuthCallbackError):
    code = "lnurl_auth_invalid_signature"
    default_message = "LNURL-auth signature is invalid."


class LNURLAuthPolicyIntentMismatchError(LNURLAuthCallbackError):
    code = "lnurl_auth_policy_intent_mismatch"
    default_message = "LNURL-auth policy intent does not match."


class LNURLAuthReplayDetectedError(LNURLAuthCallbackError):
    code = "lnurl_auth_replay_detected"
    default_message = "LNURL-auth callback could not be verified."


class LNURLAuthRateLimitedError(LNURLAuthCallbackError):
    code = "lnurl_auth_rate_limited"
    default_message = "LNURL-auth callback could not be verified at this time."


class LNURLAuthInternalVerificationError(LNURLAuthCallbackError):
    code = "lnurl_auth_internal_verification_error"
    default_message = "LNURL-auth callback verification failed safely."


class LNURLVerifyError(LNURLError):
    code = "lnurl_verify_error"
    retryable = False
    default_message = "LNURL settlement verification failed safely."

    @property
    def reason_code(self) -> str:
        return self.code


class VerifySourceUnavailableError(LNURLVerifyError):
    code = "verify_source_unavailable"
    retryable = True


class VerifyResponseMalformedError(LNURLVerifyError):
    code = "verify_response_malformed"


class VerifyURLRejectedError(LNURLVerifyError):
    code = "verify_url_rejected"


class InvoiceMismatchError(LNURLVerifyError):
    code = "invoice_mismatch"


class PaymentHashMismatchError(LNURLVerifyError):
    code = "payment_hash_mismatch"


class PaymentAmountMismatchError(LNURLVerifyError):
    code = "payment_amount_mismatch"


class PaymentNetworkMismatchError(LNURLVerifyError):
    code = "payment_network_mismatch"


class PaymentMetadataMismatchError(LNURLVerifyError):
    code = "payment_metadata_mismatch"


class PaymentPreimageMismatchError(LNURLVerifyError):
    code = "payment_preimage_mismatch"


class SettlementSourceConflictError(LNURLVerifyError):
    code = "settlement_source_conflict"


class PaymentExpiredError(LNURLVerifyError):
    code = "payment_expired"


class PaymentCanceledError(LNURLVerifyError):
    code = "payment_canceled"


class VerificationPolicyDeniedError(LNURLVerifyError):
    code = "verification_policy_denied"


class LNURLPaymentProofError(LNURLError):
    code = "lnurl_payment_proof_error"
    default_message = "LNURL payment proof operation failed safely."

    @property
    def reason_code(self) -> str:
        return self.code


class SettlementNotVerifiedError(LNURLPaymentProofError):
    code = "settlement_not_verified"


class SettlementEvidenceExpiredError(LNURLPaymentProofError):
    code = "settlement_evidence_expired"


class PaymentRequestNotFoundError(LNURLPaymentProofError):
    code = "payment_request_not_found"


class PaymentInvoiceMismatchError(LNURLPaymentProofError):
    code = "payment_invoice_mismatch"


class PaymentProductMismatchError(LNURLPaymentProofError):
    code = "payment_product_mismatch"


class PaymentAlreadyProvenError(LNURLPaymentProofError):
    code = "payment_already_proven"


class PaymentBindingInvalidError(LNURLPaymentProofError):
    code = "payment_binding_invalid"


class PaymentProofSigningError(LNURLPaymentProofError):
    code = "payment_proof_signing_failed"


class PaymentProofIntegrityError(LNURLPaymentProofError):
    code = "payment_proof_integrity_error"


class PaymentProofRevokedError(LNURLPaymentProofError):
    code = "payment_proof_revoked"
