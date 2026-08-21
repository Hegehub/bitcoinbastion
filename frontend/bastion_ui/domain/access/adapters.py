from __future__ import annotations

from bastion_ui.domain.access.models import (
    AccessChallengeViewModel,
    AccessCheckoutViewModel,
    AccessOfferViewModel,
    ChildKeyCreatedViewModel,
    IssuedAccessViewModel,
)
from bastion_ui.transport.generated_schemas import (
    AccessOfferOut,
    CheckoutOut,
    ChildApiKeyCreateResponse,
    IssuanceChallengeOut,
    IssuedAccessOut,
)


def adapt_child_key_created(response: ChildApiKeyCreateResponse) -> ChildKeyCreatedViewModel:
    """Project metadata while deliberately omitting the one-time raw child secret."""
    return ChildKeyCreatedViewModel(
        key_id=response.key_id,
        scopes=tuple(response.scopes),
        expires_at=response.expires_at,
        warning=response.warning,
    )


def adapt_access_offer(value: AccessOfferOut) -> AccessOfferViewModel:
    return AccessOfferViewModel(
        offer_id=value.offer_id, revision_id=value.revision_id,
        capability=value.capability, scopes=tuple(value.scopes),
        amount_sats=value.amount_sats, price_unit=value.price_unit,
        duration_days=value.duration_days, terms_version=value.terms_version,
        limitations=tuple(value.limitations),
    )


def adapt_access_checkout(value: CheckoutOut) -> AccessCheckoutViewModel:
    return AccessCheckoutViewModel(
        checkout_id=value.checkout_id, offer_revision_id=value.offer_revision_id,
        capability=value.capability, scopes=tuple(value.scopes),
        amount_sats=value.amount_sats, price_unit=value.price_unit,
        duration_days=value.duration_days, terms_version=value.terms_version,
        status=value.status.root,
        issuance_eligible=value.issuance_eligible,
        eligibility_reason=value.eligibility_reason.root,
        expires_at=value.expires_at,
    )


def adapt_access_challenge(value: IssuanceChallengeOut) -> AccessChallengeViewModel:
    return AccessChallengeViewModel(**value.model_dump())


def adapt_issued_access(value: IssuedAccessOut) -> IssuedAccessViewModel:
    return IssuedAccessViewModel(
        **value.model_dump(exclude={"scopes"}), scopes=tuple(value.scopes)
    )
