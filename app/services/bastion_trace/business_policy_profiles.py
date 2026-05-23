from app.schemas.bastion_trace import BusinessPolicyAction, BusinessPolicyProfile, BusinessContextType


def default_policy_profiles() -> list[BusinessPolicyProfile]:
    return [
        BusinessPolicyProfile(id="retail_low_value", name="retail_low_value", description="Retail low value baseline", context_type=BusinessContextType.RETAIL),
        BusinessPolicyProfile(id="merchant_standard", name="merchant_standard", description="Merchant baseline", context_type=BusinessContextType.MERCHANT, medium_action=BusinessPolicyAction.HOLD_FOR_REVIEW),
        BusinessPolicyProfile(id="treasury_conservative", name="treasury_conservative", description="Treasury conservative baseline", context_type=BusinessContextType.TREASURY, low_action=BusinessPolicyAction.ACCEPT_WITH_NOTE, medium_action=BusinessPolicyAction.HOLD_FOR_REVIEW, unknown_action=BusinessPolicyAction.HOLD_FOR_REVIEW),
        BusinessPolicyProfile(id="otc_strict", name="otc_strict", description="OTC strict baseline", context_type=BusinessContextType.OTC, low_action=BusinessPolicyAction.ACCEPT_WITH_NOTE, medium_action=BusinessPolicyAction.HOLD_FOR_REVIEW, critical_action=BusinessPolicyAction.REJECT_BY_POLICY),
        BusinessPolicyProfile(id="donation_platform", name="donation_platform", description="Donation platform baseline", context_type=BusinessContextType.DONATION, medium_action=BusinessPolicyAction.HOLD_FOR_REVIEW),
    ]
