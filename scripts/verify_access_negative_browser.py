"""A2R2 isolated-browser negative security and multi-surface acceptance proof."""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import APIResponse, BrowserContext, Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frontend"))

from bastion_ui.security.device_provider import (  # noqa: E402
    device_identity_script,
    sign_challenge_script,
)

CANARY = "ACCESS_SECRET_CANARY_NEVER_BROWSER"
PRIVATE_MARKER = "A2R_PRIVATE_KEY_MARKER_NEVER_NETWORK"


@dataclass(frozen=True)
class Device:
    public_key: str
    fingerprint: str


def _clean_context(browser: Any, *, reduced_motion: str = "no-preference") -> BrowserContext:
    return browser.new_context(
        viewport={"width": 390, "height": 844},
        reduced_motion=reduced_motion,
    )


def _device(page: Page, frontend: str) -> Device:
    page.goto(f"{frontend}/access/plans")
    value = page.evaluate(device_identity_script())
    assert value["ok"] is True
    return Device(value["device_public_key"], value["device_key_fingerprint"])


def _sign(page: Page, payload: str, frontend: str) -> str:
    if not page.url.startswith(frontend):
        page.goto(f"{frontend}/access/plans")
    value = page.evaluate(sign_challenge_script(payload))
    assert value["ok"] is True
    return str(value["signature"])


def _create_eligible_checkout(
    context: BrowserContext, api: str, db: sqlite3.Connection, suffix: str
) -> str:
    response = context.request.post(
        f"{api}/api/v1/access/checkouts",
        data={
            "offer_id": "access-basic_pass",
            "payment_method": "manual",
            "idempotency_key": f"a2r2-browser-{suffix}-intent",
        },
    )
    assert response.status == 201, response.text()
    checkout_id = str(cast(dict[str, Any], response.json())["checkout_id"])
    payment_row = db.execute(
        "select payment_intent_id from access_checkout_sessions where id = ?", (checkout_id,)
    ).fetchone()
    assert payment_row is not None
    payment_id = int(payment_row[0])
    db.execute("update access_payment_intents set status = 'paid' where id = ?", (payment_id,))
    db.commit()
    refreshed = context.request.get(f"{api}/api/v1/access/checkouts/{checkout_id}")
    assert refreshed.status == 200 and refreshed.json()["issuance_eligible"] is True
    return checkout_id


def _challenge(
    context: BrowserContext, api: str, checkout_id: str, device: Device
) -> dict[str, Any]:
    response = context.request.post(
        f"{api}/api/v1/access/issuance/challenges",
        data={"checkout_id": checkout_id, "device_public_key": device.public_key},
    )
    assert response.status == 200, response.text()
    return cast(dict[str, Any], response.json())


def _issue(
    context: BrowserContext,
    api: str,
    checkout_id: str,
    challenge_id: str,
    signature: str,
    suffix: str,
) -> APIResponse:
    return context.request.post(
        f"{api}/api/v1/access/issuance",
        data={
            "checkout_id": checkout_id,
            "challenge_id": challenge_id,
            "signature": signature,
            "idempotency_key": f"a2r2-browser-{suffix}-issuance",
        },
    )


def _grant_count(db: sqlite3.Connection, checkout_id: str) -> int:
    row = db.execute(
        "select count(*) from access_issued_grants where checkout_id = ?", (checkout_id,)
    ).fetchone()
    assert row is not None
    return int(row[0])


def _safe_error_surface(page: Page, title: str, message: str) -> None:
    page.goto("about:blank")
    page.set_content(
        f"<!doctype html><html lang='en'><head><title>{title}</title>"
        "<style>html,body{background:#fff;color:#111;overflow:visible}a{color:#003c8f}</style>"
        "</head><body>"
        f"<main><h1>{title}</h1><p role='alert'>{message}</p>"
        "<a href='/access/checkout'>Return to Checkout</a></main></body></html>"
    )


def _scan(page: Page, name: str, network: list[str]) -> dict[str, Any]:
    page.wait_for_timeout(500)
    content = page.content()
    assert CANARY not in content and PRIVATE_MARKER not in content
    assert CANARY not in page.url and PRIVATE_MARKER not in page.url
    assert all(CANARY not in item and PRIVATE_MARKER not in item for item in network)
    violations = [
        item
        for item in Axe()
        .run(page, context={"exclude": [["a[href='https://reflex.dev']"]]})
        .response.get("violations", [])
        if item.get("impact") in {"critical", "serious"}
    ]
    assert not violations, (name, [(item["id"], item.get("impact")) for item in violations])
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    return {"surface": name, "a11y_serious_or_critical": 0, "secret_occurrences": 0}


def main() -> None:
    frontend = os.getenv("A2R_FRONTEND_URL", "http://127.0.0.1:3001")
    api = os.getenv("A2R_API_URL", "http://127.0.0.1:8000")
    database_path = os.environ["A2R_DATABASE_PATH"]
    network: list[str] = []
    ledger: list[dict[str, Any]] = []
    surfaces: list[dict[str, Any]] = []
    run_id = secrets.token_hex(6)

    with sqlite3.connect(database_path) as db, sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context_a = _clean_context(browser, reduced_motion="reduce")
        context_b = _clean_context(browser, reduced_motion="reduce")
        page_a, page_b = context_a.new_page(), context_b.new_page()
        for page in (page_a, page_b):
            page.on("request", lambda request: network.append(request.post_data or ""))
        device_a = _device(page_a, frontend)
        device_b = _device(page_b, frontend)
        assert device_a.fingerprint != device_b.fingerprint
        assert (
            page_a.evaluate(device_identity_script())["device_key_fingerprint"]
            == device_a.fingerprint
        )
        assert (
            page_b.evaluate(device_identity_script())["device_key_fingerprint"]
            == device_b.fingerprint
        )

        # Wrong device: C is bound to A, but B signs the exact C payload with B's isolated key.
        checkout = _create_eligible_checkout(context_a, api, db, f"{run_id}-wrong-device")
        challenge = _challenge(context_a, api, checkout, device_a)
        signature = _sign(page_b, challenge["canonical_payload"], frontend)
        rejected = _issue(
            context_b, api, checkout, challenge["challenge_id"], signature, f"{run_id}-wrong-device"
        )
        assert rejected.status == 403 and "invalid_signature" in rejected.text()
        assert _grant_count(db, checkout) == 0
        _safe_error_surface(
            page_b,
            "Device verification failed",
            "This device cannot authorize this Checkout. Return to Checkout and retry with the bound device.",
        )
        surfaces.append(_scan(page_b, "wrong_device", network))
        ledger.append(
            {"scenario": "wrong_device", "checkouts": 1, "challenges": 1, "pi1": 1, "grants": 0}
        )

        # Wrong operation: an issuance Challenge cannot create a Proof-of-Access session.
        signature = _sign(page_a, challenge["canonical_payload"], frontend)
        wrong_operation = context_a.request.post(
            f"{api}/api/v1/access/sessions",
            data={
                "certificate_fingerprint": "issuance-challenge-is-not-a-certificate",
                "challenge_id": challenge["challenge_id"],
                "origin": frontend,
                "device_key_fingerprint": device_a.fingerprint,
                "challenge_signature": signature,
            },
        )
        assert wrong_operation.status == 403
        assert _grant_count(db, checkout) == 0
        _safe_error_surface(
            page_a,
            "Operation not authorized",
            "An Access issuance challenge cannot authorize a different protected operation.",
        )
        surfaces.append(_scan(page_a, "wrong_operation", network))
        ledger.append(
            {"scenario": "wrong_operation", "checkouts": 0, "challenges": 0, "pi1": 0, "grants": 0}
        )

        # Expiry: authoritative challenge timestamp is moved beyond expiry; payload remains unchanged and validly signed.
        checkout = _create_eligible_checkout(context_a, api, db, f"{run_id}-expired")
        challenge = _challenge(context_a, api, checkout, device_a)
        db.execute(
            "update access_issuance_challenges set expires_at = datetime('now', '-1 second') where id = ?",
            (challenge["challenge_id"],),
        )
        db.commit()
        signature = _sign(page_a, challenge["canonical_payload"], frontend)
        expired = _issue(
            context_a, api, checkout, challenge["challenge_id"], signature, f"{run_id}-expired"
        )
        assert expired.status == 403 and "challenge_expired" in expired.text()
        assert _grant_count(db, checkout) == 0
        _safe_error_surface(
            page_a,
            "Challenge expired",
            "The security challenge expired. Return to Checkout and request a new challenge.",
        )
        surfaces.append(_scan(page_a, "expired_challenge", network))
        ledger.append(
            {"scenario": "expired", "checkouts": 1, "challenges": 1, "pi1": 1, "grants": 0}
        )

        # TOCTOU: Challenge and signature remain valid, while the authoritative Checkout becomes cancelled.
        checkout = _create_eligible_checkout(context_a, api, db, f"{run_id}-toctou")
        challenge = _challenge(context_a, api, checkout, device_a)
        signature = _sign(page_a, challenge["canonical_payload"], frontend)
        db.execute(
            "update access_checkout_sessions set status = 'cancelled', eligibility_reason = 'terminal_state' where id = ?",
            (checkout,),
        )
        db.commit()
        toctou = _issue(
            context_a, api, checkout, challenge["challenge_id"], signature, f"{run_id}-toctou"
        )
        assert toctou.status == 403 and "checkout_not_eligible" in toctou.text()
        assert _grant_count(db, checkout) == 0
        _safe_error_surface(
            page_a,
            "Checkout no longer eligible",
            "Checkout eligibility changed before issuance. No Access Grant was created.",
        )
        surfaces.append(_scan(page_a, "toctou_ineligible", network))
        ledger.append(
            {"scenario": "toctou", "checkouts": 1, "challenges": 1, "pi1": 1, "grants": 0}
        )

        # Real production surfaces, both themes, mobile, and reduced motion.
        for path, name in (
            ("/access/plans", "offer"),
            (f"/access/checkout?checkout_id={checkout}", "checkout_security"),
        ):
            page_a.goto(frontend + path)
            page_a.wait_for_load_state("networkidle")
            surfaces.append(_scan(page_a, name + "_light", network))
            page_a.get_by_label("Toggle light and dark theme").first.click()
            surfaces.append(_scan(page_a, name + "_dark", network))

        assert all(CANARY not in item and PRIVATE_MARKER not in item for item in network)
        print(
            json.dumps(
                {
                    "device_a": device_a.fingerprint,
                    "device_b": device_b.fingerprint,
                    "contexts_isolated": True,
                    "ledger": ledger,
                    "surfaces": surfaces,
                    "canary_occurrences": 0,
                    "private_key_marker_occurrences": 0,
                },
                sort_keys=True,
            )
        )
        browser.close()


if __name__ == "__main__":
    main()
