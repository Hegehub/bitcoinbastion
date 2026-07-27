"""Privacy-preserving Wallet-first authentication metrics."""

from app.services.access.observability import (
    DURATION_BUCKETS,
    metric_counter,
    metric_gauge,
    metric_histogram,
    safe_inc,
    safe_observe,
    safe_set,
)
from app.services.access.observability_labels import (
    ActionGroupLabel,
    ActorTypeLabel,
    AuthMethodLabel,
    EndpointGroupLabel,
    ReasonCodeLabel,
    ResultLabel,
    normalize_label,
)

WALLET_AUTH_CHALLENGES = metric_counter(
    "wallet_auth_challenges_total",
    "Wallet challenge outcomes.",
    ["action", "network", "proof_type", "result"],
)
WALLET_AUTH_PROOFS = metric_counter(
    "wallet_auth_proofs_total",
    "Wallet proof verification outcomes.",
    ["action", "proof_type", "verification_strength", "network", "result", "reason_code"],
)
WALLET_AUTH_REGISTRATIONS = metric_counter(
    "wallet_auth_registrations_total",
    "Wallet registration outcomes.",
    ["proof_type", "network", "result", "reason_code"],
)
WALLET_AUTH_LOGINS = metric_counter(
    "wallet_auth_logins_total",
    "Wallet login outcomes.",
    ["proof_type", "verification_strength", "network", "result", "reason_code"],
)
WALLET_PRINCIPALS = metric_counter(
    "wallet_principals_total",
    "Aggregate Wallet Principal creation attempts.",
    ["principal_type", "result"],
)
WALLET_DEVICE_BINDINGS = metric_counter(
    "wallet_device_bindings_total",
    "Wallet device binding outcomes.",
    ["device_class", "binding_method", "result", "reason_code"],
)
WALLET_DEVICE_REVOCATIONS = metric_counter(
    "wallet_device_revocations_total", "Wallet device revocations.", ["device_class", "reason_code"]
)
WALLET_DEVICES_ACTIVE = metric_gauge(
    "wallet_devices_active", "Aggregate active wallet devices.", ["device_class", "status"]
)
WALLET_POP_SESSIONS = metric_counter(
    "wallet_pop_sessions_total",
    "Wallet PoP session outcomes.",
    ["actor_type", "auth_method", "plan", "result", "reason_code"],
)
WALLET_POP_SESSIONS_ACTIVE = metric_gauge(
    "wallet_pop_sessions_active", "Aggregate active PoP sessions.", ["actor_type", "plan"]
)
WALLET_POP_SESSION_DURATION = metric_histogram(
    "wallet_pop_session_duration_seconds",
    "PoP session duration.",
    ["actor_type", "plan", "result"],
    buckets=DURATION_BUCKETS,
)
WALLET_POP_REQUEST_VERIFICATIONS = metric_counter(
    "wallet_pop_request_verifications_total",
    "PoP request verification outcomes.",
    ["actor_type", "endpoint_group", "result", "reason_code"],
)
WALLET_POP_REPLAY_REJECTIONS = metric_counter(
    "wallet_pop_replay_rejections_total", "PoP replay rejections.", ["replay_type", "auth_method"]
)
WALLET_STEP_UP_REQUESTS = metric_counter(
    "wallet_step_up_requests_total",
    "Wallet step-up outcomes.",
    ["action_group", "auth_method", "risk_level", "result", "reason_code"],
)
WALLET_STEP_UP_DURATION = metric_histogram(
    "wallet_step_up_duration_seconds",
    "Wallet step-up duration.",
    ["action_group", "auth_method", "result"],
    buckets=DURATION_BUCKETS,
)
WALLET_STEP_UP_REQUIRED = metric_counter(
    "wallet_step_up_required_total",
    "Policy-required Wallet step-up.",
    ["action_group", "actor_type", "risk_level", "policy_reason"],
)
QUORUM_CREATED = metric_counter(
    "bastion_quorum_created_total",
    "Wallet/LNURL quorum creation outcomes.",
    ["quorum_type", "action_group", "result", "reason_code"],
)
QUORUM_APPROVALS = metric_counter(
    "bastion_quorum_approvals_total",
    "Wallet/LNURL quorum approval outcomes.",
    ["quorum_type", "action_group", "result", "reason_code"],
)
QUORUM_DECISIONS = metric_counter(
    "bastion_quorum_decisions_total",
    "Wallet/LNURL final quorum decisions.",
    ["quorum_type", "action_group", "result", "reason_code"],
)

_ACTIONS = {"register", "login", "link", "auth", "step_up", "unknown"}
_NETWORKS = {"mainnet", "testnet", "signet", "regtest", "unknown"}
_PROOFS = {
    "bip322",
    "legacy_message_signature",
    "hardware_wallet",
    "air_gapped",
    "multisig_quorum",
    "unknown",
}
_STRENGTH = {"compatibility", "standard", "high_assurance", "sovereign", "unknown"}
_DEVICE_CLASSES = {"software", "hardware_backed", "browser_extension", "payregister", "unknown"}
_BINDING_METHODS = {"bip322", "lnurl_auth", "access_certificate", "recovery", "unknown"}
_RISK = {"low", "medium", "high", "critical", "unknown"}
_REPLAY = {"challenge", "k1", "request_nonce", "timestamp", "session", "unknown"}


def _label(value: object, allowed: set[str]) -> str:
    candidate = str(value or "unknown").lower()
    return candidate if candidate in allowed else "unknown"


class WalletMetrics:
    def challenge(
        self, *, action: object, network: object, proof_type: object, result: object
    ) -> None:
        safe_inc(
            WALLET_AUTH_CHALLENGES,
            {
                "action": _label(action, _ACTIONS),
                "network": _label(network, _NETWORKS),
                "proof_type": _label(proof_type, _PROOFS),
                "result": normalize_label(result, ResultLabel),
            },
        )

    def proof(
        self,
        *,
        action: object,
        proof_type: object,
        verification_strength: object,
        network: object,
        result: object,
        reason_code: object,
    ) -> None:
        safe_inc(
            WALLET_AUTH_PROOFS,
            {
                "action": _label(action, _ACTIONS),
                "proof_type": _label(proof_type, _PROOFS),
                "verification_strength": _label(verification_strength, _STRENGTH),
                "network": _label(network, _NETWORKS),
                "result": normalize_label(result, ResultLabel),
                "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            },
        )

    def pop_request(
        self, *, actor_type: object, endpoint: object, result: object, reason_code: object
    ) -> None:
        safe_inc(
            WALLET_POP_REQUEST_VERIFICATIONS,
            {
                "actor_type": normalize_label(actor_type, ActorTypeLabel),
                "endpoint_group": normalize_label(endpoint, EndpointGroupLabel),
                "result": normalize_label(result, ResultLabel),
                "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            },
        )

    def replay(self, *, replay_type: object, auth_method: object) -> None:
        safe_inc(
            WALLET_POP_REPLAY_REJECTIONS,
            {
                "replay_type": _label(replay_type, _REPLAY),
                "auth_method": normalize_label(auth_method, AuthMethodLabel),
            },
        )

    def step_up(
        self,
        *,
        action_group: object,
        auth_method: object,
        risk_level: object,
        result: object,
        reason_code: object,
        duration_seconds: float | None = None,
    ) -> None:
        labels = {
            "action_group": normalize_label(action_group, ActionGroupLabel),
            "auth_method": normalize_label(auth_method, AuthMethodLabel),
            "risk_level": _label(risk_level, _RISK),
            "result": normalize_label(result, ResultLabel),
        }
        safe_inc(
            WALLET_STEP_UP_REQUESTS,
            {**labels, "reason_code": normalize_label(reason_code, ReasonCodeLabel)},
        )
        if duration_seconds is not None:
            safe_observe(
                WALLET_STEP_UP_DURATION,
                {key: labels[key] for key in ("action_group", "auth_method", "result")},
                duration_seconds,
            )

    def set_active_devices(self, *, device_class: object, status: object, count: int) -> None:
        safe_set(
            WALLET_DEVICES_ACTIVE,
            {
                "device_class": _label(device_class, _DEVICE_CLASSES),
                "status": _label(status, {"active", "suspended", "revoked", "unknown"}),
            },
            count,
        )


class WalletQuorumMetrics:
    """Low-cardinality sink for the quorum coordinator."""

    _METRICS = {
        "bastion_quorum_created_total": QUORUM_CREATED,
        "bastion_quorum_approvals_total": QUORUM_APPROVALS,
        "bastion_quorum_decisions_total": QUORUM_DECISIONS,
    }
    _TYPES = {
        "single_principal",
        "multi_wallet",
        "multi_method",
        "role_based",
        "recovery",
        "business",
        "enterprise",
        "sovereign",
        "payregister",
        "withdraw",
        "issuer_rotation",
        "pq_migration",
        "unknown",
    }
    _RESULTS = {
        "pending",
        "partially_satisfied",
        "satisfied",
        "allow",
        "deny",
        "expired",
        "revoked",
        "unknown",
    }
    _REASONS = {
        "created",
        "quorum_pending",
        "quorum_satisfied",
        "quorum_authorized",
        "insufficient_distinct_principals",
        "insufficient_distinct_methods",
        "required_role_missing",
        "required_quorum_evidence_missing",
        "unknown",
    }

    def record(self, name: str, labels: dict[str, str]) -> None:
        metric = self._METRICS.get(name)
        if metric is None:
            return
        safe_inc(
            metric,
            {
                "quorum_type": _label(labels.get("quorum_type"), self._TYPES),
                "action_group": normalize_label(labels.get("action_group"), ActionGroupLabel),
                "result": _label(labels.get("result"), self._RESULTS),
                "reason_code": _label(labels.get("reason_code"), self._REASONS),
            },
        )
