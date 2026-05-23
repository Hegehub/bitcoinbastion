from app.schemas.bastion_trace import EnterpriseCapability, EnterpriseTierProfile


def get_enterprise_tier_profile() -> EnterpriseTierProfile:
    return EnterpriseTierProfile(
        tier="ENTERPRISE",
        capabilities=[
            EnterpriseCapability.ENTERPRISE_RBAC_PLACEHOLDER,
            EnterpriseCapability.SSO_PLACEHOLDER,
            EnterpriseCapability.LEGAL_HOLD,
            EnterpriseCapability.IMMUTABLE_AUDIT_LOG,
            EnterpriseCapability.SIEM_HOOKS,
            EnterpriseCapability.RETENTION_POLICY,
            EnterpriseCapability.EVIDENCE_ACCESS_GOVERNANCE,
            EnterpriseCapability.ENTERPRISE_PROOF_PACKET,
            EnterpriseCapability.ORG_POLICY_PLACEHOLDER,
            EnterpriseCapability.APPROVAL_WORKFLOW_PLACEHOLDER,
        ],
        limits={"billing_enforced": False},
        feature_flags={"enterprise_baseline": True},
        limitations=["enterprise_capability_profile_not_billing_enforcement"],
    )
