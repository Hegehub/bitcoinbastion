"""Real-stack Prompt-11R acceptance with ephemeral Device-bound PoP.

Secrets exist only in process memory/environment. Output contains a truncated public
device fingerprint and redacted request metadata, never auth/proof headers.
"""

from __future__ import annotations

import base64
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
DB = ROOT / "prompt11r-browser.db"
PEPPER = secrets.token_urlsafe(32)
TOKEN = "sess_" + secrets.token_urlsafe(32)
SIMILARITY_PATH = "/api/v1/market/similarity/1"


def _wait(url: str, timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server unavailable: {url}")


def _seed(private_key: Ed25519PrivateKey) -> str:
    os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
    os.environ["ACCESS_SERVER_PEPPER"] = PEPPER
    from app.db import models as _models  # noqa: F401
    from app.db.base import Base
    from app.db.models.access import (
        AccessCertificate,
        AccessDevice,
        AccessSession,
        SubscriptionEntitlement,
    )
    from app.db.models.historical_event_similarity import HistoricalEventSimilarity
    from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
    from app.db.models.news_event import NewsEvent
    from app.db.session import SessionLocal, engine
    from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed

    Base.metadata.create_all(engine)
    now = datetime(2026, 8, 12, 12)
    expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15)
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    fingerprint = sha256_prefixed(public_raw)
    certificate = "sha256:" + secrets.token_hex(32)
    pass_hash = "hmac-sha256:" + secrets.token_hex(32)
    with SessionLocal() as db:
        entitlement = SubscriptionEntitlement(
            pass_lookup_hash=pass_hash,
            certificate_fingerprint=certificate,
            plan_code="business_pass",
            status="active",
            metric_entitlements_json={},
            limits_json={},
            scopes_json=["market:intelligence:read"],
            issuer_signature_json={},
            crypto_epoch=1,
            valid_from=datetime.now(UTC).replace(tzinfo=None),
            valid_until=expires,
        )
        db.add(entitlement)
        db.flush()
        db.add_all(
            [
                AccessDevice(
                    certificate_fingerprint=certificate,
                    device_key_fingerprint=fingerprint,
                    device_public_key=base64.urlsafe_b64encode(public_raw).decode().rstrip("="),
                    device_class="browser_test",
                    status="active",
                    first_seen_at=now,
                    last_seen_at=now,
                    risk_score=0,
                ),
                AccessCertificate(
                    pass_lookup_hash=pass_hash,
                    pass_commitment="sha256:" + secrets.token_hex(32),
                    certificate_fingerprint=certificate,
                    plan_code="business_pass",
                    status="active",
                    device_key_fingerprint=fingerprint,
                    issuer_key_id="browser-test",
                    crypto_epoch=1,
                    scopes_json=["market:intelligence:read"],
                    issuer_signature_json={},
                    issued_at=now,
                    expires_at=expires,
                ),
                AccessSession(
                    session_hash=hmac_sha256_prefixed(PEPPER, TOKEN),
                    certificate_fingerprint=certificate,
                    device_key_fingerprint=fingerprint,
                    entitlement_id=entitlement.id,
                    scopes_json=["market:intelligence:read"],
                    policy_context_json={"requires_request_signing": True},
                    status="active",
                    risk_level="low",
                    created_at=now,
                    updated_at=now,
                    expires_at=expires,
                ),
                NewsEvent(
                    id=1,
                    canonical_title="Current integration context",
                    event_type="MARKET",
                    event_category="MARKET",
                    first_seen_at=now,
                    last_seen_at=now,
                ),
                NewsEvent(
                    id=2,
                    canonical_title="Persisted historical analog",
                    event_type="MARKET",
                    event_category="MARKET",
                    first_seen_at=now - timedelta(days=30),
                    last_seen_at=now - timedelta(days=30),
                ),
                *(
                    NewsEvent(
                        id=event_id,
                        canonical_title=f"Eligible historical context {event_id}",
                        event_type="MARKET",
                        event_category="MARKET",
                        first_seen_at=now - timedelta(days=event_id * 10),
                        last_seen_at=now - timedelta(days=event_id * 10),
                    )
                    for event_id in range(3, 7)
                ),
                IntelligenceTimelineEvent(
                    id=2,
                    event_type="market_event",
                    source_kind="INTERNAL",
                    related_event_id=2,
                    title="Persisted historical analog",
                    summary="Authoritative integration replay capture.",
                    event_time=now - timedelta(days=30),
                    ingested_at=now - timedelta(days=30),
                ),
            ]
        )
        db.flush()
        db.add_all(
            HistoricalEventSimilarity(
                id=10 + offset,
                event_id=1,
                similar_event_id=event_id,
                similarity_score=score,
                pattern_match=event_id == 2,
                sentiment_match=max(score - 0.125, 0),
                impact_match=max(score - 0.25, 0),
                volatility_match=max(score - 0.375, 0),
            )
            for offset, (event_id, score) in enumerate(
                ((2, 0.875), (3, 0.8), (4, 0.7), (5, 0.6), (6, 0.5)), 1
            )
        )
        db.commit()
    return fingerprint


def main() -> None:
    DB.unlink(missing_ok=True)
    for suffix in ("-wal", "-shm"):
        Path(str(DB) + suffix).unlink(missing_ok=True)
    private_key = Ed25519PrivateKey.generate()
    private_text = base64.urlsafe_b64encode(
        private_key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
    ).decode().rstrip("=")
    fingerprint = _seed(private_key)
    env = os.environ | {
        "DATABASE_URL": f"sqlite:///{DB}",
        "ACCESS_SERVER_PEPPER": PEPPER,
        "P9_BROWSER_POP_BOOTSTRAP": "1",
        "BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE": "ephemeral-device-pop-v1",
        "P9_TEST_SESSION_TOKEN": TOKEN,
        "P9_TEST_DEVICE_PRIVATE_KEY": private_text,
        "PYTHONPATH": (
            f"{ROOT / 'tests/browser_support'}:{FRONTEND}:{ROOT}:"
            f"{os.environ.get('PYTHONPATH', '')}"
        ),
    }
    with tempfile.TemporaryFile(mode="w+") as backend_log:
        processes = [
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--access-log"],
                cwd=ROOT,
                env=env,
                stdout=backend_log,
                stderr=subprocess.STDOUT,
            ),
            subprocess.Popen(
                [str(FRONTEND / ".venv/bin/reflex"), "run", "--frontend-port", "3000", "--backend-port", "8001"],
                cwd=FRONTEND,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ),
        ]
        try:
            _wait("http://127.0.0.1:8000/health")
            assert httpx.get(f"http://127.0.0.1:8000{SIMILARITY_PATH}").status_code == 401
            _wait("http://127.0.0.1:3000/market/similarity")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto("http://127.0.0.1:3000/market/similarity", wait_until="networkidle")
                if not page.locator(".similarity-title").count():
                    page.wait_for_timeout(5000)
                if not page.locator(".similarity-title").count():
                    print("DEBUG similarity body:", page.locator("body").inner_text()[:1200])
                page.locator(".similarity-title", has_text="Persisted historical analog").wait_for()
                assert "Rank 1" in page.locator(".similarity-title").first.inner_text()
                assert "0.875" in page.locator(".similarity-score").first.inner_text()
                assert "NOT_PREDICTIVE" in page.locator(".similarity-meaning").first.inner_text()
                assert page.get_by_text("WEIGHTED_EVENT_CONTEXT_V1", exact=True).count() == 1
                assert "0.54 to 0.845" in page.locator(".similarity-interval-text").inner_text()
                assert page.locator(".similarity-interval-ribbon").is_visible()
                page.get_by_text("View accessible analytical data", exact=True).click()
                interval_row = page.get_by_role("table", name="Similarity analytical data table")
                assert "0.54" in interval_row.inner_text() and "0.845" in interval_row.inner_text()
                page.screenshot(path="/tmp/p11r-feature20.png", full_page=True)
                page.get_by_role("link", name="Open canonical historical replay").first.focus()
                page.keyboard.press("Enter")
                page.wait_for_url("**/market/time-machine/2")
                page.locator("#replay-capture-id").wait_for()
                assert "Persisted historical analog" in page.locator("body").inner_text()
                page.go_back(wait_until="networkidle")
                page.locator(".similarity-title", has_text="Persisted historical analog").wait_for()
                page.go_forward(wait_until="networkidle")
                page.locator("#replay-capture-id").wait_for()
                page.go_back(wait_until="networkidle")
                page.locator(".similarity-title", has_text="Persisted historical analog").wait_for()
                page.set_viewport_size({"width": 390, "height": 844})
                bounds = page.locator(".similarity-title").first.bounding_box()
                assert bounds is not None and bounds["x"] + bounds["width"] <= 390
                page.reload(wait_until="networkidle")
                page.locator(".similarity-title", has_text="Persisted historical analog").wait_for()
                browser.close()
        finally:
            for process in reversed(processes):
                process.send_signal(signal.SIGINT)
            for process in reversed(processes):
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
        backend_log.seek(0)
        log = backend_log.read()
        requests = log.count(f'GET {SIMILARITY_PATH}?limit=10 HTTP/1.1" 200')
        assert requests == 4, f"expected initial/back/back/refresh requests, got {requests}"
        assert TOKEN not in log and private_text not in log
        print(
            "PASS similarity_pop "
            f"fingerprint={fingerprint[:18]}… scope=market:intelligence:read"
        )
        print(
            "PASS similarity_live operation=market_similarity_report "
            f"path={SIMILARITY_PATH} status=200 requests={requests} unexpected_duplicates=0"
        )
        print(
            "PASS similarity_dom rank=1 score=0.875 method=v1 replay_event_id=2 "
            "interval=EMPIRICAL_QUANTILE_INTERVAL[0.54,0.845] leaks=0"
        )
    DB.unlink(missing_ok=True)
    for suffix in ("-wal", "-shm"):
        Path(str(DB) + suffix).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
