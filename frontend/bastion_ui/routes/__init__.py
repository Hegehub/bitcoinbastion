from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import reflex as rx

from bastion_ui.routes.access import (
    access_certificate_page,
    access_checkout_page,
    access_offline_page,
    access_page,
    access_payment_page,
    access_payment_pending_page,
    access_plans_page,
    access_success_page,
)
from bastion_ui.routes.access_extensions import (
    business_access_page,
    business_devices_page,
    business_security_page,
    register_access_page,
    register_devices_page,
    register_refunds_page,
)
from bastion_ui.routes.check import check_page
from bastion_ui.routes.developers import developers_page
from bastion_ui.routes.docs import docs_page
from bastion_ui.routes.evidence import evidence_page
from bastion_ui.routes.home import home_page
from bastion_ui.routes.lnurl import lnurl_auth_page, lnurl_pay_page, lnurl_payment_status_page
from bastion_ui.routes.manifesto import manifesto_page
from bastion_ui.routes.operations import operations_page
from bastion_ui.routes.platform import platform_page
from bastion_ui.routes.roadmap import roadmap_page
from bastion_ui.routes.security import security_page
from bastion_ui.routes.status import status_page
from bastion_ui.routes.trace import trace_page
from bastion_ui.routes.wallet_auth import (
    wallet_auth_page,
    wallet_bitcoin_page,
    wallet_devices_page,
    wallet_entitlements_page,
    wallet_lightning_addresses_page,
    wallet_lightning_page,
    wallet_lightning_pay_page,
    wallet_lightning_withdraw_page,
    wallet_lnurl_page,
    wallet_lockdown_page,
    wallet_login_page,
    wallet_recovery_page,
    wallet_register_page,
    wallet_security_page,
    wallet_session_page,
    wallet_step_up_page,
    wallet_subscription_page,
)


@dataclass(frozen=True)
class PublicRouteSpec:
    route: str
    title: str
    page: Callable[[], rx.Component]


PUBLIC_ROUTE_SPECS: tuple[PublicRouteSpec, ...] = (
    PublicRouteSpec("/", "Bitcoin Bastion", home_page),
    PublicRouteSpec("/platform", "Platform", platform_page),
    PublicRouteSpec("/access", "Bastion Access", access_page),
    PublicRouteSpec("/access/plans", "Access Plans", access_plans_page),
    PublicRouteSpec("/access/checkout", "Access Checkout", access_checkout_page),
    PublicRouteSpec("/access/payment", "Payment", access_payment_page),
    PublicRouteSpec("/access/payment/pending", "Payment Pending", access_payment_pending_page),
    PublicRouteSpec("/access/payment/success", "Access Success", access_success_page),
    PublicRouteSpec("/access/certificate", "Access Certificate", access_certificate_page),
    PublicRouteSpec("/access/offline", "Offline Validity", access_offline_page),
    PublicRouteSpec("/wallet-auth", "Wallet Authentication", wallet_auth_page),
    PublicRouteSpec("/wallet-auth/register", "Wallet Registration", wallet_register_page),
    PublicRouteSpec("/wallet-auth/login", "Wallet Login", wallet_login_page),
    PublicRouteSpec("/wallet-auth/lnurl", "Lightning Login", wallet_lnurl_page),
    PublicRouteSpec("/wallet-auth/bitcoin", "Bitcoin Wallet Login", wallet_bitcoin_page),
    PublicRouteSpec("/wallet-auth/session", "PoP Session", wallet_session_page),
    PublicRouteSpec("/wallet-auth/devices", "Devices", wallet_devices_page),
    PublicRouteSpec("/wallet-auth/entitlements", "Entitlements", wallet_entitlements_page),
    PublicRouteSpec("/wallet-auth/subscription", "Subscription", wallet_subscription_page),
    PublicRouteSpec("/wallet-auth/step-up", "Step-up", wallet_step_up_page),
    PublicRouteSpec("/wallet-auth/recovery", "Recovery Capsule", wallet_recovery_page),
    PublicRouteSpec("/wallet-auth/lockdown", "Emergency Lockdown", wallet_lockdown_page),
    PublicRouteSpec("/wallet-auth/lightning", "Lightning Wallet", wallet_lightning_page),
    PublicRouteSpec("/wallet-auth/lightning/pay", "Lightning Payment", wallet_lightning_pay_page),
    PublicRouteSpec(
        "/wallet-auth/lightning/withdraw", "Lightning Withdraw", wallet_lightning_withdraw_page
    ),
    PublicRouteSpec(
        "/wallet-auth/lightning/addresses", "Lightning Addresses", wallet_lightning_addresses_page
    ),
    PublicRouteSpec("/wallet-auth/security", "Wallet Security", wallet_security_page),
    PublicRouteSpec("/lnurl/auth", "LNURL-auth", lnurl_auth_page),
    PublicRouteSpec("/lnurl/pay", "LNURL-pay", lnurl_pay_page),
    PublicRouteSpec("/lnurl/payment-status", "LNURL Payment Status", lnurl_payment_status_page),
    PublicRouteSpec("/business/access", "Business Access", business_access_page),
    PublicRouteSpec("/business/devices", "Business Devices", business_devices_page),
    PublicRouteSpec("/business/security", "Business Security", business_security_page),
    PublicRouteSpec("/register/access", "PayRegister Access", register_access_page),
    PublicRouteSpec("/register/devices", "PayRegister Devices", register_devices_page),
    PublicRouteSpec("/register/refunds", "PayRegister Refunds", register_refunds_page),
    PublicRouteSpec("/check", "Check Bitcoin Address", check_page),
    PublicRouteSpec("/trace", "Bastion Trace", trace_page),
    PublicRouteSpec("/developers", "Developers", developers_page),
    PublicRouteSpec("/operations", "Operations", operations_page),
    PublicRouteSpec("/manifesto", "Manifesto", manifesto_page),
    PublicRouteSpec("/evidence", "Evidence", evidence_page),
    PublicRouteSpec("/status", "Status", status_page),
    PublicRouteSpec("/roadmap", "Roadmap", roadmap_page),
    PublicRouteSpec("/security", "Security", security_page),
    PublicRouteSpec("/docs", "Docs", docs_page),
)
