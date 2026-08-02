"""Privacy-minimizing adapters for transparency source records.

Adapters accept already verified service facts and commit only canonical hashes,
coarse classes, and epochs. They never copy raw protocol records into leaves.
"""

from datetime import datetime
from typing import Any, Mapping

from .canonicalization import canonical_commitment
from .models import TransparencyLeafCommitment
from .privacy import validate_source_metadata


def _leaf(
    leaf_type: str,
    source: Mapping[str, Any],
    *,
    event_time: datetime,
    object_epoch: int,
    policy_hash: str,
    context: str,
) -> TransparencyLeafCommitment:
    committed_source = {
        key: value
        for key, value in source.items()
        if key not in {"event_time", "object_epoch", "policy_hash", "context"}
    }
    validate_source_metadata(committed_source, public_safe=True)
    return TransparencyLeafCommitment(
        leaf_type=leaf_type,
        object_hash=canonical_commitment(committed_source, context=f"{context}:object"),
        object_version=1,
        object_epoch=object_epoch,
        event_time=event_time,
        policy_hash=policy_hash,
        status_commitment=canonical_commitment(
            {"status": committed_source.get("status", "committed")}, context=f"{context}:status"
        ),
        metadata_commitment=canonical_commitment(committed_source, context=f"{context}:metadata"),
    )


def issuer_key_epoch_commitment(
    *, key_id_hash: str, crypto_epoch: int, status: str, signature_suite: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("issuer_key", locals(), event_time=event_time, object_epoch=crypto_epoch, policy_hash="sha256:none", context="issuer-key")


def policy_epoch_commitment(
    *, policy_bundle_hash: str, policy_epoch: int, schema_version: int, environment: str, event_time: datetime
) -> TransparencyLeafCommitment:
    source = {"policy_bundle_hash": policy_bundle_hash, "schema_version": schema_version, "environment": environment, "status": "active"}
    return _leaf("policy", source, event_time=event_time, object_epoch=policy_epoch, policy_hash=policy_bundle_hash, context="policy")


def revocation_epoch_commitment(
    *, registry_root_hash: str, revocation_epoch: int, entry_count: int, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("revocation", {"registry_root_hash": registry_root_hash, "entry_count": entry_count, "status": "active"}, event_time=event_time, object_epoch=revocation_epoch, policy_hash="sha256:none", context="revocation")


def wallet_credential_commitment(
    *, credential_commitment: str, proof_method: str, status: str, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("wallet_credential", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="wallet-credential")


def lightning_principal_commitment(
    *, principal_commitment: str, auth_domain_hash: str, proof_method: str, verification_strength: str, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("lightning_principal_batch", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="lightning-principal")


def entitlement_commitment(
    *, entitlement_fingerprint: str, plan_commitment: str, validity_commitment: str, status: str, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("subscription_entitlement_batch", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="entitlement")


def access_certificate_commitment(
    *, certificate_fingerprint: str, expiry_commitment: str, status: str, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("access_certificate_batch", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="access-certificate")


def recovery_event_commitment(
    *, recovery_event_hash: str, profile: str, outcome: str, cooldown_class: str, quorum_class: str, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("recovery_event", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="recovery-event")


def offline_pack_epoch_commitment(
    *, pack_epoch: int, issuer_epoch: int, revocation_epoch: int, policy_epoch: int, validity_window_commitment: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("offline_validity_pack", locals(), event_time=event_time, object_epoch=pack_epoch, policy_hash=f"epoch:{policy_epoch}", context="offline-pack")


def lnurl_payment_proof_commitment(
    *, proof_fingerprint: str, payment_status_commitment: str, entitlement_commitment_hash: str, payment_method: str, settlement_method: str, amount_bucket: str | None, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("lnurl_payment_proof", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="lnurl-payment")


def lnurl_withdraw_commitment(
    *, request_fingerprint: str, decision_hash: str, payout_status_commitment: str, amount_bucket: str | None, role_class: str, object_epoch: int, policy_hash: str, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("lnurl_withdraw_batch", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=policy_hash, context="lnurl-withdraw")


def lightning_address_registry_commitment(
    *, route_commitment: str, domain_hash: str, routing_policy_hash: str, status: str, template_hash: str, object_epoch: int, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("lightning_address_registry", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=routing_policy_hash, context="lightning-address")


def wallet_compatibility_registry_commitment(
    *, registry_hash: str, supported_methods_hash: str, risk_policy_hash: str, object_epoch: int, event_time: datetime
) -> TransparencyLeafCommitment:
    return _leaf("wallet_compatibility_registry", locals(), event_time=event_time, object_epoch=object_epoch, policy_hash=risk_policy_hash, context="wallet-compatibility")
