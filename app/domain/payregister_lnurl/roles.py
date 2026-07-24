"""Workspace-scoped PayRegister actor and cashier roles."""
from __future__ import annotations

from enum import StrEnum


class PayRegisterActorType(StrEnum):
    MERCHANT_OWNER = "merchant_owner"
    MERCHANT_ADMIN = "merchant_admin"
    STORE_MANAGER = "store_manager"
    CASHIER = "cashier"
    TERMINAL_DEVICE = "terminal_device"
    UNATTENDED_TERMINAL = "unattended_terminal"
    INTEGRATION_BOT = "integration_bot"


class PayRegisterCashierRole(StrEnum):
    CASHIER = "cashier"
    SENIOR_CASHIER = "senior_cashier"
    SHIFT_SUPERVISOR = "shift_supervisor"
    STORE_MANAGER = "store_manager"
