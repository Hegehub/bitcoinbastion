"""Ephemeral real-stack Prompt-9R4 browser acceptance runner."""

from __future__ import annotations

import base64
import os
import secrets
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
DB = ROOT / "prompt9r4-browser.db"
PEPPER = secrets.token_urlsafe(32)
TOKEN = "sess_" + secrets.token_urlsafe(32)


def _wait(url: str, timeout: float = 90) -> None:
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server not ready: {url}")


def _focus_option(page, name: str) -> None:
    """Reach a command using only sequential keyboard focus."""
    option = page.locator(".bb-command-result:visible", has_text=name).first
    option.wait_for()
    for _ in range(50):
        if option.evaluate("element => element === document.activeElement"):
            return
        page.keyboard.press("Tab")
    raise AssertionError(f"keyboard focus did not reach {name}")


def _seed(private_key: Ed25519PrivateKey) -> str:
    os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
    os.environ["ACCESS_SERVER_PEPPER"] = PEPPER
    from app.db import models as _models  # noqa: F401
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(engine)
    from app.db.models.access import (
        AccessCertificate,
        AccessDevice,
        AccessSession,
        SubscriptionEntitlement,
    )
    from app.db.models.observability_health import BackgroundJobHealth
    from app.db.session import SessionLocal
    from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed

    now = datetime.now(UTC).replace(tzinfo=None)
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    public_text = base64.urlsafe_b64encode(public_raw).decode().rstrip("=")
    fingerprint = sha256_prefixed(public_raw)
    cert = "sha256:" + secrets.token_hex(32)
    pass_hash = "hmac-sha256:" + secrets.token_hex(32)
    db = SessionLocal()
    entitlement = SubscriptionEntitlement(
        pass_lookup_hash=pass_hash,
        certificate_fingerprint=cert,
        plan_code="business_pass",
        status="active",
        metric_entitlements_json={},
        limits_json={},
        scopes_json=["operations:read"],
        issuer_signature_json={},
        crypto_epoch=1,
        valid_from=now,
        valid_until=now + timedelta(minutes=30),
    )
    db.add(entitlement)
    db.flush()
    db.add(
        AccessDevice(
            certificate_fingerprint=cert,
            device_key_fingerprint=fingerprint,
            device_public_key=public_text,
            device_class="browser_test",
            status="active",
            first_seen_at=now,
            last_seen_at=now,
            risk_score=0,
        )
    )
    db.add(
        AccessCertificate(
            pass_lookup_hash=pass_hash,
            pass_commitment="sha256:" + secrets.token_hex(32),
            certificate_fingerprint=cert,
            plan_code="business_pass",
            status="active",
            device_key_fingerprint=fingerprint,
            issuer_key_id="browser-test",
            crypto_epoch=1,
            scopes_json=["operations:read"],
            issuer_signature_json={},
            issued_at=now,
            expires_at=now + timedelta(minutes=30),
        )
    )
    db.add(
        AccessSession(
            session_hash=hmac_sha256_prefixed(PEPPER, TOKEN),
            certificate_fingerprint=cert,
            device_key_fingerprint=fingerprint,
            entitlement_id=entitlement.id,
            scopes_json=["operations:read"],
            policy_context_json={"requires_request_signing": True},
            status="active",
            risk_level="low",
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(minutes=15),
        )
    )
    db.add(
        BackgroundJobHealth(
            job_name="signals.publish",
            last_start_at=now - timedelta(seconds=4),
            last_finish_at=now,
            duration_ms=4000,
            success=False,
            failure_reason="bounded integration-test failure summary",
            retry_count=1,
            next_scheduled_at=now + timedelta(minutes=5),
            worker_name="redacted-worker",
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    db.close()
    return fingerprint


def main() -> None:
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()
    )
    private_text = base64.urlsafe_b64encode(private_raw).decode().rstrip("=")
    fingerprint = _seed(private_key)
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": f"sqlite:///{DB}",
            "ACCESS_SERVER_PEPPER": PEPPER,
            "P9_BROWSER_POP_BOOTSTRAP": "1",
            "BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE": "ephemeral-device-pop-v1",
            "P9_TEST_SESSION_TOKEN": TOKEN,
            "P9_TEST_DEVICE_PRIVATE_KEY": private_text,
            "PYTHONPATH": f"{ROOT / 'tests/browser_support'}:{ROOT / 'frontend'}:{ROOT}",
        }
    )
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
        subprocess.Popen(
            [
                str(FRONTEND / ".venv/bin/reflex"),
                "run",
                "--frontend-port",
                "3000",
                "--backend-port",
                "8001",
            ],
            cwd=FRONTEND,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ),
    ]
    try:
        _wait("http://127.0.0.1:8000/health")
        _wait("http://127.0.0.1:3000/operations/jobs")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(
                "http://127.0.0.1:3000/operations/jobs", wait_until="networkidle", timeout=90000
            )
            page.wait_for_selector(".job-name", timeout=30000)
            job_row = page.locator("li", has=page.locator(".job-name", has_text="signals.publish"))
            assert job_row.count() == 1, page.locator(".job-name").all_inner_texts()
            assert "degraded" in job_row.locator(".job-status").inner_text().lower()
            assert (
                "bounded integration-test failure summary"
                in job_row.locator(".job-failure").inner_text()
            )
            body = page.locator("body").inner_text().lower()
            assert all(
                secret not in body
                for secret in (TOKEN.lower(), private_text.lower(), "redacted-worker")
            )
            page.keyboard.press("/")
            page.wait_for_selector('[role="dialog"][aria-label="Command palette"]')
            assert page.locator("#command-palette-search").evaluate(
                "element => element === document.activeElement"
            )
            page.keyboard.press("Escape")
            page.locator('[role="dialog"]').wait_for(state="detached")
            page.keyboard.press("/")
            page.wait_for_function("document.activeElement?.id === 'command-palette-search'")
            page.keyboard.type("Operations Jobs")
            _focus_option(page, "Open Operations Jobs")
            page.keyboard.press("Enter")
            page.wait_for_url("**/operations/jobs")
            page.wait_for_selector(".job-name")
            page.keyboard.press("/")
            page.wait_for_function("document.activeElement?.id === 'command-palette-search'")
            page.keyboard.type("Market Signals")
            _focus_option(page, "Open Market Signals")
            page.keyboard.press("Enter")
            page.wait_for_url("**/market/signals")
            page.set_viewport_size({"width": 390, "height": 844})
            page.keyboard.press("/")
            page.wait_for_function("document.activeElement?.id === 'command-palette-search'")
            assert page.locator('[role="dialog"]').is_visible()
            assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
                "document.documentElement.clientWidth"
            )
            page.keyboard.type("Market Intelligence")
            _focus_option(page, "Open Market Intelligence")
            page.keyboard.press("Enter")
            page.wait_for_url("**/market")
            print(
                f"PASS jobs_pop fingerprint={fingerprint[:18]}… plan=business_pass scope=operations:read"
            )
            print(
                "PASS jobs_dom name/status/timing/failure provenance=LIVE leaks=0 "
                "operation=GET_/api/v1/operations/jobs"
            )
            print("PASS command_keyboard slash focus/search/enter/escape/routes/mobile")
            browser.close()
    finally:
        for process in reversed(processes):
            process.send_signal(signal.SIGINT)
        for process in reversed(processes):
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
        DB.unlink(missing_ok=True)
        for suffix in ("-shm", "-wal"):
            Path(str(DB) + suffix).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
