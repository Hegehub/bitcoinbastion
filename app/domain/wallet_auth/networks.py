"""Wallet network domain primitives for wallet-first auth."""

from __future__ import annotations

from enum import StrEnum


class WalletNetwork(StrEnum):
    BITCOIN_MAINNET = "bitcoin-mainnet"
    BITCOIN_TESTNET = "bitcoin-testnet"
    BITCOIN_SIGNET = "bitcoin-signet"
    BITCOIN_REGTEST = "bitcoin-regtest"


DEFAULT_PRODUCTION_NETWORK = WalletNetwork.BITCOIN_MAINNET
_TEST_NETWORKS = frozenset(
    {
        WalletNetwork.BITCOIN_TESTNET,
        WalletNetwork.BITCOIN_SIGNET,
        WalletNetwork.BITCOIN_REGTEST,
    }
)


def is_production_network(network: WalletNetwork | str) -> bool:
    return WalletNetwork(network) is WalletNetwork.BITCOIN_MAINNET


def is_test_network(network: WalletNetwork | str) -> bool:
    return WalletNetwork(network) in _TEST_NETWORKS
