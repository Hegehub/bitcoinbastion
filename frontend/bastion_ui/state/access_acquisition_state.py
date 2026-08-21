# ruff: noqa: E501
"""Canonical safe State for Offer → Checkout → WebCrypto → PI1 → Grant."""

from __future__ import annotations

import secrets
from typing import Any

import httpx
import reflex as rx

from bastion_ui.config import get_config
from bastion_ui.domain.access.adapters import (
    adapt_access_challenge,
    adapt_access_checkout,
    adapt_access_offer,
    adapt_issued_access,
)
from bastion_ui.domain.access.models import (
    AccessChallengeViewModel,
    AccessCheckoutViewModel,
    AccessOfferViewModel,
    IssuedAccessViewModel,
)
from bastion_ui.security.device_provider import device_identity_script, sign_challenge_script
from bastion_ui.transport.foundation import HttpTransport, SafeTransportError
from bastion_ui.transport.generated_http import (
    CreateAccessCheckoutApiV1AccessCheckoutsPostRequest,
    CreateIssuanceChallengeApiV1AccessIssuanceChallengesPostRequest,
    GetAccessCheckoutApiV1AccessCheckoutsCheckoutIdGetRequest,
    GetAccessOffersApiV1AccessOffersGetRequest,
    GetIssuedAccessApiV1AccessIssuedGrantIdGetRequest,
    IssueAccessApiV1AccessIssuancePostRequest,
    create_access_checkout_api_v1_access_checkouts_post,
    create_issuance_challenge_api_v1_access_issuance_challenges_post,
    get_access_checkout_api_v1_access_checkouts__checkout_id__get,
    get_access_offers_api_v1_access_offers_get,
    get_issued_access_api_v1_access_issued__grant_id__get,
    issue_access_api_v1_access_issuance_post,
)
from bastion_ui.transport.generated_schemas import (
    AccessIssueRequest,
    CheckoutCreateRequest,
    IssuanceChallengeCreateRequest,
)


class AccessAcquisitionState(rx.State):
    offers: list[AccessOfferViewModel] = []
    selected_offer_id: str = ""
    checkout: AccessCheckoutViewModel | None = None
    challenge: AccessChallengeViewModel | None = None
    issued_access: IssuedAccessViewModel | None = None
    offer_status: str = "idle"
    checkout_status: str = "idle"
    security_status: str = "idle"
    issuance_status: str = "idle"
    safe_error: str = ""
    device_public_key: str = ""
    device_key_fingerprint: str = ""
    signature: str = ""
    generation: int = 0
    checkout_in_flight: bool = False
    challenge_in_flight: bool = False
    issuance_in_flight: bool = False

    async def load_route(self) -> None:
        self.generation += 1
        self.clear_ephemeral()
        grant_id = self.router.page.params.get("grant_id", "").strip()
        checkout_id = self.router.page.params.get("checkout_id", "").strip()
        if grant_id:
            await self.load_grant(grant_id)
        elif checkout_id:
            await self.load_checkout(checkout_id)
        else:
            await self.load_offers()

    async def load_offers(self) -> None:
        token = self.generation
        self.offer_status = "loading"
        try:
            async with self._client() as client:
                result = await get_access_offers_api_v1_access_offers_get(
                    HttpTransport(client), GetAccessOffersApiV1AccessOffersGetRequest()
                )
            if token != self.generation:
                return
            self.offers = [adapt_access_offer(item) for item in result.root]
            self.offer_status = "success" if self.offers else "unavailable"
        except SafeTransportError:
            if token == self.generation:
                self.offer_status = "unavailable"
                self.safe_error = "Access Offers are unavailable. No placeholder terms were substituted."

    def select_offer(self, offer_id: str) -> None:
        self.selected_offer_id = offer_id

    async def create_checkout(self) -> Any:
        if self.checkout_in_flight or not self.selected_offer_id:
            return None
        self.checkout_in_flight = True
        self.checkout_status = "loading"
        self.safe_error = ""
        offer_id = self.selected_offer_id
        token = self.generation
        intent = f"access-ui-{secrets.token_urlsafe(24)}"
        try:
            async with self._client() as client:
                result = await create_access_checkout_api_v1_access_checkouts_post(
                    HttpTransport(client),
                    CreateAccessCheckoutApiV1AccessCheckoutsPostRequest(
                        body=CheckoutCreateRequest(
                            offer_id=offer_id, payment_method="manual", idempotency_key=intent
                        )
                    ),
                )
            if token != self.generation or offer_id != self.selected_offer_id:
                return None
            self.checkout = adapt_access_checkout(result.root)
            self.checkout_status = "success"
            return rx.redirect(f"/access/checkout?checkout_id={self.checkout.checkout_id}")
        except SafeTransportError:
            if token == self.generation:
                self.checkout_status = "error"
                self.safe_error = "Checkout could not be created. No payment or eligibility was assumed."
        finally:
            if token == self.generation:
                self.checkout_in_flight = False
        return None

    async def load_checkout(self, checkout_id: str) -> None:
        token = self.generation
        self.checkout_status = "loading"
        try:
            async with self._client() as client:
                result = await get_access_checkout_api_v1_access_checkouts__checkout_id__get(
                    HttpTransport(client),
                    GetAccessCheckoutApiV1AccessCheckoutsCheckoutIdGetRequest(
                        checkout_id=checkout_id
                    ),
                )
            if token == self.generation:
                self.checkout = adapt_access_checkout(result.root)
                self.checkout_status = "success"
        except SafeTransportError:
            if token == self.generation:
                self.checkout_status = "error"
                self.safe_error = "Checkout is unavailable or expired."

    def begin_secure_issuance(self) -> Any:
        if (
            self.challenge_in_flight
            or self.issuance_in_flight
            or self.checkout is None
            or not self.checkout.issuance_eligible
        ):
            return None
        self.security_status = "preparing_device"
        return rx.call_script(
            device_identity_script(), callback=AccessAcquisitionState.receive_device_identity
        )

    def receive_device_identity(self, result: dict[str, Any]) -> Any:
        if not result.get("ok"):
            self.security_status = "unavailable"
            self.safe_error = "Secure device signing is unavailable; no insecure fallback is permitted."
            return None
        self.device_public_key = str(result["device_public_key"])
        self.device_key_fingerprint = str(result["device_key_fingerprint"])
        return type(self).create_challenge

    async def create_challenge(self) -> Any:
        if self.challenge_in_flight or self.checkout is None or not self.device_public_key:
            return None
        self.challenge_in_flight = True
        self.security_status = "creating_challenge"
        checkout_id = self.checkout.checkout_id
        token = self.generation
        try:
            async with self._client() as client:
                result = await create_issuance_challenge_api_v1_access_issuance_challenges_post(
                    HttpTransport(client),
                    CreateIssuanceChallengeApiV1AccessIssuanceChallengesPostRequest(
                        body=IssuanceChallengeCreateRequest(
                            checkout_id=checkout_id, device_public_key=self.device_public_key
                        )
                    ),
                )
            if token != self.generation or self.checkout is None or checkout_id != self.checkout.checkout_id:
                return None
            self.challenge = adapt_access_challenge(result.root)
            self.security_status = "signing"
            return rx.call_script(
                sign_challenge_script(self.challenge.canonical_payload),
                callback=AccessAcquisitionState.receive_signature,
            )
        except SafeTransportError:
            if token == self.generation:
                self.security_status = "error"
                self.safe_error = "The device challenge could not be created."
        finally:
            if token == self.generation:
                self.challenge_in_flight = False
        return None

    def receive_signature(self, result: dict[str, Any]) -> Any:
        if not result.get("ok") or self.challenge is None:
            self.security_status = "error"
            self.safe_error = "Device signing failed without exposing key material."
            return None
        self.signature = str(result["signature"])
        self.security_status = "signed"
        return type(self).submit_pi1

    async def submit_pi1(self) -> Any:
        if self.issuance_in_flight or self.checkout is None or self.challenge is None or not self.signature:
            return None
        self.issuance_in_flight = True
        self.issuance_status = "issuing"
        token = self.generation
        checkout_id = self.checkout.checkout_id
        challenge_id = self.challenge.challenge_id
        try:
            async with self._client() as client:
                result = await issue_access_api_v1_access_issuance_post(
                    HttpTransport(client),
                    IssueAccessApiV1AccessIssuancePostRequest(
                        body=AccessIssueRequest(
                            checkout_id=checkout_id,
                            challenge_id=challenge_id,
                            signature=self.signature,
                            idempotency_key=f"pi1-{secrets.token_urlsafe(24)}",
                        )
                    ),
                )
            if token != self.generation or self.checkout is None or checkout_id != self.checkout.checkout_id:
                return None
            self.issued_access = adapt_issued_access(result.root)
            self.issuance_status = "success"
            self.clear_ephemeral(preserve_status=True)
            return rx.redirect(f"/access/payment/success?grant_id={self.issued_access.grant_id}")
        except SafeTransportError:
            if token == self.generation:
                self.issuance_status = "error"
                self.safe_error = "Access issuance was rejected. Refresh Checkout status before retrying."
        finally:
            if token == self.generation:
                self.issuance_in_flight = False
        return None

    async def load_grant(self, grant_id: str) -> None:
        token = self.generation
        self.issuance_status = "loading"
        try:
            async with self._client() as client:
                result = await get_issued_access_api_v1_access_issued__grant_id__get(
                    HttpTransport(client),
                    GetIssuedAccessApiV1AccessIssuedGrantIdGetRequest(grant_id=grant_id),
                )
            if token == self.generation:
                self.issued_access = adapt_issued_access(result.root)
                self.issuance_status = "success"
        except SafeTransportError:
            if token == self.generation:
                self.issuance_status = "error"
                self.safe_error = "Issued Access could not be loaded."

    def clear_ephemeral(self, *, preserve_status: bool = False) -> None:
        self.challenge = None
        self.signature = ""
        self.device_public_key = ""
        self.device_key_fingerprint = ""
        self.challenge_in_flight = False
        self.issuance_in_flight = False
        if not preserve_status:
            self.security_status = "idle"

    @staticmethod
    def _client() -> httpx.AsyncClient:
        config = get_config()
        return httpx.AsyncClient(
            base_url=config.api_base_url, timeout=config.request_timeout_seconds
        )
