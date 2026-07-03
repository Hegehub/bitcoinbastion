from app.schemas.bastion_trace import EnterprisePermission, EnterpriseRole, RbacPolicyPlaceholder


def default_rbac_policy() -> RbacPolicyPlaceholder:
    return RbacPolicyPlaceholder(
        role_permissions={
            EnterpriseRole.OWNER: list(EnterprisePermission),
            EnterpriseRole.ADMIN: [
                EnterprisePermission.TRACE_READ,
                EnterprisePermission.TRACE_CREATE,
                EnterprisePermission.TRACE_BATCH_CREATE,
                EnterprisePermission.TRACE_REVIEW_DECIDE,
                EnterprisePermission.TRACE_POLICY_MANAGE,
                EnterprisePermission.TRACE_EXPORT_CREATE,
                EnterprisePermission.TRACE_AUDIT_READ,
            ],
            EnterpriseRole.ANALYST: [
                EnterprisePermission.TRACE_READ,
                EnterprisePermission.TRACE_CREATE,
                EnterprisePermission.TRACE_BATCH_CREATE,
            ],
            EnterpriseRole.REVIEWER: [
                EnterprisePermission.TRACE_READ,
                EnterprisePermission.TRACE_REVIEW_DECIDE,
            ],
            EnterpriseRole.AUDITOR: [
                EnterprisePermission.TRACE_READ,
                EnterprisePermission.TRACE_AUDIT_READ,
            ],
            EnterpriseRole.READ_ONLY: [EnterprisePermission.TRACE_READ],
        },
        production_enforced=False,
        limitations=["RBAC_NOT_PRODUCTION_ENFORCED"],
    )
