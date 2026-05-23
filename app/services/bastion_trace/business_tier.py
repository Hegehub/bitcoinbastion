from app.schemas.bastion_trace import BusinessCapability, BusinessTierProfile


def get_business_tier_profile() -> BusinessTierProfile:
    return BusinessTierProfile(
        tier="BUSINESS",
        capabilities=[
            BusinessCapability.BATCH_SCREENING,
            BusinessCapability.BUSINESS_POLICY_PROFILES,
            BusinessCapability.REVIEW_DESK,
            BusinessCapability.OPERATOR_NOTES,
            BusinessCapability.PROOF_PACKET_EXPORT,
            BusinessCapability.ACCOUNTING_EXPORT,
            BusinessCapability.WATCHLIST_GROUPS,
            BusinessCapability.WEBHOOK_PLACEHOLDER,
            BusinessCapability.REGISTER_INTEGRATION_PLACEHOLDER,
            BusinessCapability.TREASURY_INTEGRATION_PLACEHOLDER,
            BusinessCapability.API_KEY_SCOPE_PLACEHOLDER,
        ],
        limits={"billing_enforced": False, "max_addresses_per_batch": 1000},
        feature_flags={"business_baseline": True},
        limitations=["business_tier_capability_profile_not_billing_enforcement"],
    )
