"""Access scope constants for Bastion Proof-of-Access Auth."""

from __future__ import annotations

METRICS_BASIC_READ = "metrics:basic:read"
MARKET_PRICE_READ = "market:price:read"
MARKET_OHLCV_READ = "market:ohlcv:read"
MARKET_VOLATILITY_READ = "market:volatility:read"
BITCOIN_NETWORK_READ = "bitcoin:network:read"
BITCOIN_MEMPOOL_READ = "bitcoin:mempool:read"
BITCOIN_FEES_READ = "bitcoin:fees:read"
BITCOIN_BLOCKS_READ = "bitcoin:blocks:read"
MEMPOOL_FEES_READ = "mempool:fees:read"
RISK_MARKET_READ = "risk:market:read"
MARKET_INTELLIGENCE_READ = "market:intelligence:read"
MARKET_REGIME_READ = "market:regime:read"
MARKET_LIQUIDITY_READ = "market:liquidity:read"
SIGNALS_LITE_READ = "signals:lite:read"
SIGNALS_STANDARD_READ = "signals:standard:read"
SIGNALS_ADVANCED_READ = "signals:advanced:read"
HISTORICAL_SIMILARITY_READ = "historical:similarity:read"
HISTORICAL_CYCLES_READ = "historical:cycles:read"
TIMEMACHINE_QUERY = "timemachine:query"
TRACE_LITE_READ = "trace:lite:read"
TRACE_STANDARD_READ = "trace:standard:read"
TRACE_ADVANCED_READ = "trace:advanced:read"
PRIVACY_ANALYSIS_READ = "privacy:analysis:read"
PRIVACY_ANALYSIS_ADVANCED = "privacy:analysis:advanced"
WALLET_HEALTH_BASIC = "wallet:health:basic"
WALLET_HEALTH_READ = "wallet:health:read"
TREASURY_READ = "treasury:read"
TREASURY_POLICY_READ = "treasury:policy:read"
PSBT_ANALYSIS_READ = "psbt:analysis:read"
API_READ = "api:read"
API_KEYS_READ = "api:keys:read"
API_KEYS_MANAGE = "api:keys:manage"
DELEGATED_PASS_CREATE = "delegated_pass:create"
EVIDENCE_PACKET_CREATE = "evidence:packet:create"
ACCESS_USAGE_READ = "access:usage:read"
ACCESS_INTEGRITY_READ = "access:integrity:read"
ALERTS_MANAGE = "alerts:manage"
BUSINESS_WORKSPACE = "business:workspace"
BUSINESS_AUDIT_READ = "business:audit:read"
BUSINESS_ROLES_MANAGE = "business:roles:manage"
PAYREGISTER_PAYMENT_CREATE = "payregister:payment:create"
PAYREGISTER_REFUND_REQUEST = "payregister:refund:request"
PAYREGISTER_METRICS_READ = "payregister:metrics:read"
PAYREGISTER_OPERATOR_READ = "payregister:operator:read"
PAYREGISTER_DEVICES_READ = "payregister:devices:read"
PAYREGISTER_SHIFTS_READ = "payregister:shifts:read"
PAYREGISTER_INVOICES_READ = "payregister:invoices:read"
PAYREGISTER_ADMIN = "payregister:admin"
ENTERPRISE_WORKSPACE = "enterprise:workspace"
ENTERPRISE_POLICY_CUSTOM = "enterprise:policy:custom"
ENTERPRISE_QUOTA_CUSTOM = "enterprise:quota:custom"
ENTERPRISE_METRICS_CUSTOM = "enterprise:metrics:custom"
ENTERPRISE_AUDIT_EXPORT = "enterprise:audit:export"
ENTERPRISE_PRIVATE_DEPLOYMENT = "enterprise:private_deployment"
TRANSPARENCY_CHECKPOINT_READ = "transparency:checkpoint:read"

REFUNDS_SUBSCRIPTION_CREATE = "refunds:subscription:create"
REFUNDS_SUBSCRIPTION_APPROVE = "refunds:subscription:approve"
REFUNDS_PAYREGISTER_CREATE = "refunds:payregister:create"
REFUNDS_PAYREGISTER_APPROVE = "refunds:payregister:approve"
PAYOUTS_CASHBACK_CREATE = "payouts:cashback:create"
PAYOUTS_PARTNER_CREATE = "payouts:partner:create"
PAYOUTS_PARTNER_APPROVE = "payouts:partner:approve"
PAYOUTS_BOUNTY_CREATE = "payouts:bounty:create"
PAYOUTS_BOUNTY_APPROVE = "payouts:bounty:approve"
PAYOUTS_EXECUTE = "payouts:execute"
LNURL_WITHDRAW_READ = "lnurl:withdraw:read"
LNURL_WITHDRAW_CREATE = "lnurl:withdraw:create"
LNURL_WITHDRAW_APPROVE = "lnurl:withdraw:approve"
LNURL_WITHDRAW_CANCEL = "lnurl:withdraw:cancel"

ACCESS_SCOPES: frozenset[str] = frozenset(
    {
        METRICS_BASIC_READ,
        MARKET_PRICE_READ,
        MARKET_OHLCV_READ,
        MARKET_VOLATILITY_READ,
        BITCOIN_NETWORK_READ,
        BITCOIN_MEMPOOL_READ,
        BITCOIN_FEES_READ,
        BITCOIN_BLOCKS_READ,
        MEMPOOL_FEES_READ,
        RISK_MARKET_READ,
        MARKET_INTELLIGENCE_READ,
        MARKET_REGIME_READ,
        MARKET_LIQUIDITY_READ,
        SIGNALS_LITE_READ,
        SIGNALS_STANDARD_READ,
        SIGNALS_ADVANCED_READ,
        HISTORICAL_SIMILARITY_READ,
        HISTORICAL_CYCLES_READ,
        TIMEMACHINE_QUERY,
        TRACE_LITE_READ,
        TRACE_STANDARD_READ,
        TRACE_ADVANCED_READ,
        PRIVACY_ANALYSIS_READ,
        PRIVACY_ANALYSIS_ADVANCED,
        WALLET_HEALTH_BASIC,
        WALLET_HEALTH_READ,
        TREASURY_READ,
        TREASURY_POLICY_READ,
        PSBT_ANALYSIS_READ,
        API_READ,
        API_KEYS_READ,
        API_KEYS_MANAGE,
        DELEGATED_PASS_CREATE,
        EVIDENCE_PACKET_CREATE,
        ACCESS_USAGE_READ,
        ACCESS_INTEGRITY_READ,
        ALERTS_MANAGE,
        BUSINESS_WORKSPACE,
        BUSINESS_AUDIT_READ,
        BUSINESS_ROLES_MANAGE,
        PAYREGISTER_PAYMENT_CREATE,
        PAYREGISTER_REFUND_REQUEST,
        PAYREGISTER_METRICS_READ,
        PAYREGISTER_OPERATOR_READ,
        PAYREGISTER_DEVICES_READ,
        PAYREGISTER_SHIFTS_READ,
        PAYREGISTER_INVOICES_READ,
        PAYREGISTER_ADMIN,
        ENTERPRISE_WORKSPACE,
        ENTERPRISE_POLICY_CUSTOM,
        ENTERPRISE_QUOTA_CUSTOM,
        ENTERPRISE_METRICS_CUSTOM,
        ENTERPRISE_AUDIT_EXPORT,
        ENTERPRISE_PRIVATE_DEPLOYMENT,
        TRANSPARENCY_CHECKPOINT_READ,
        LNURL_WITHDRAW_CANCEL,
        LNURL_WITHDRAW_APPROVE,
        LNURL_WITHDRAW_CREATE,
        LNURL_WITHDRAW_READ,
        PAYOUTS_EXECUTE,
        PAYOUTS_BOUNTY_APPROVE,
        PAYOUTS_BOUNTY_CREATE,
        PAYOUTS_PARTNER_APPROVE,
        PAYOUTS_PARTNER_CREATE,
        PAYOUTS_CASHBACK_CREATE,
        REFUNDS_PAYREGISTER_APPROVE,
        REFUNDS_PAYREGISTER_CREATE,
        REFUNDS_SUBSCRIPTION_APPROVE,
        REFUNDS_SUBSCRIPTION_CREATE,
    }
)

FORBIDDEN_SCOPES: frozenset[str] = frozenset({"api:all", "metrics:all", "admin:all", "*", "root", "superuser"})
