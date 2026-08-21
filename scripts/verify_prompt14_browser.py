#!/usr/bin/env python3
"""Reproducible Prompt-14 historical, network, privacy, and a11y browser proof."""

from __future__ import annotations

import base64
from collections.abc import Iterator
from collections import Counter
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import cast
from urllib.request import urlopen

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path[:0] = [str(ROOT), str(FRONTEND)]
ADDRESS = "bc1qexampleaddress0000000000000000000000000"
CANARY = "TRACE_EVIDENCE_PRIVACY_CANARY_NEVER_BROWSER"
LINEAGE_CANARY = "TRACE_EVIDENCE_LINEAGE_PRIVACY_CANARY_NEVER_BROWSER"


def _wait(url: str, timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1):  # noqa: S310 - fixed loopback harness URL
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server did not become ready: {url}")


def _seed(database_url: str) -> dict[str, object]:
    os.environ["DATABASE_URL"] = database_url
    from fastapi.testclient import TestClient

    from app.api.dependencies import db_session
    from app.api.v1.trace import _proof_packet_or_404
    from app.db.base import Base
    from app.db.repositories.bastion_trace_repository import BastionTraceRepository
    from app.db.repositories.onchain_repository import OnchainRepository
    from app.db.session import SessionLocal, engine
    from app.integrations.bitcoin.provider import ChainEvent
    from app.main import app
    from app.services.bastion_trace.trace_service import TraceService
    from app.services.bitcoin_observations.producer import BitcoinObservationProducer

    Base.metadata.create_all(engine)
    session = SessionLocal()
    try:
        report = TraceService(BastionTraceRepository(session)).analyze_address(ADDRESS)
        assert report.id is not None
        report_id = report.id

        def override_db() -> Iterator[object]:
            yield session

        app.dependency_overrides[db_session] = override_db
        client = TestClient(app)
        producer = BitcoinObservationProducer(OnchainRepository(session))

        def add_event(txid: str, minute: int) -> None:
            producer.persist_chain_event(
                ChainEvent(
                    event_type="large_transfer",
                    txid=txid,
                    address=ADDRESS,
                    value_sats=21_000 + minute,
                    block_height=900_300 + minute,
                    observed_at=datetime(2026, 8, 15, tzinfo=UTC) + timedelta(minutes=minute),
                    payload={
                        "provider": "bitcoin_core_rpc",
                        "source_type": "rpc",
                        "network": "bitcoin-mainnet",
                        "server_only_canary": CANARY,
                        "lineage_server_only_canary": LINEAGE_CANARY,
                    },
                ),
                significance=0.5,
                confidence=0.8,
            )

        add_event("prompt14-snapshot-a", 0)
        assert client.get(f"/api/v1/trace/report/{report_id}/graph/snapshot").status_code == 200
        history_a = client.get(f"/api/v1/trace/report/{report_id}/graph/history").json()["data"]
        snapshot_a = history_a["entries"][-1]["snapshot_id"]
        packet_a_before = _proof_packet_or_404(report_id, snapshot_a, True, session)

        add_event("prompt14-snapshot-b", 1)
        assert client.get(f"/api/v1/trace/report/{report_id}/graph/snapshot").status_code == 200
        history_b = client.get(f"/api/v1/trace/report/{report_id}/graph/history").json()["data"]
        snapshot_b = next(
            item["snapshot_id"]
            for item in reversed(history_b["entries"])
            if item["snapshot_id"] != snapshot_a
        )
        packet_b = _proof_packet_or_404(report_id, snapshot_b, True, session)
        packet_a_after = _proof_packet_or_404(report_id, snapshot_a, True, session)
        packet_current = _proof_packet_or_404(report_id, None, False, session)
        assert packet_a_before == packet_a_after
        evidence_a = {item.evidence_id for item in packet_a_after.evidence}
        evidence_b = {item.evidence_id for item in packet_b.evidence}
        b_only = sorted(evidence_b - evidence_a)
        assert b_only, "Snapshot B must have canonical B-only Evidence"
        return {
            "report_id": report_id,
            "snapshot_a": snapshot_a,
            "snapshot_b": snapshot_b,
            "packet_a": packet_a_after.packet_id,
            "packet_b": packet_b.packet_id,
            "packet_current": packet_current.packet_id,
            "a_evidence": sorted(evidence_a)[-1],
            "b_only_evidence": b_only[0],
        }
    finally:
        app.dependency_overrides.clear()
        session.close()


def _axe(page: Page, label: str) -> dict[str, object]:
    results = Axe().run(page, context="#trace-proof-packet")
    violations = [
        {
            "id": item["id"],
            "impact": item.get("impact"),
            "targets": [node["target"] for node in item["nodes"]],
        }
        for item in results.response["violations"]
    ]
    if violations:
        raise AssertionError(f"axe violations for {label}: {violations}")
    return {"label": label, "violations": 0}


def _body(page: Page) -> str:
    return cast(str, page.locator("body").inner_text())


def _wait_packet(page: Page, packet_id: str) -> str:
    try:
        page.get_by_text(packet_id, exact=True).wait_for(timeout=30_000)
    except Exception as exc:
        raise AssertionError(
            f"packet {packet_id} did not render at {page.url}: {_body(page)[:2000]}"
        ) from exc
    return _body(page)


def _packet_counts(ledger: Path) -> Counter[str]:
    paths = ledger.read_text().splitlines() if ledger.exists() else []
    return Counter(path for path in paths if "proof-packet" in path)


def _workflow_counts(ledger: Path) -> Counter[str]:
    paths = ledger.read_text().splitlines() if ledger.exists() else []
    return Counter(
        path
        for path in paths
        if "/evidence/" in path
        and path.rsplit("/", 1)[-1] in {"lineage", "replay", "verification", "export"}
    )


def main() -> None:
    reflex_executable = str(FRONTEND / ".venv/bin/reflex")
    if not Path(reflex_executable).exists():
        reflex_executable = shutil.which("reflex") or ""
    if not Path(reflex_executable).exists():
        raise RuntimeError("reflex executable is unavailable")
    with tempfile.TemporaryDirectory(prefix="bastion-p14r-") as directory:
        temp = Path(directory)
        database_url = f"sqlite:///{temp / 'prompt14.db'}"
        ledger = temp / "requests.log"
        delay_flag = temp / "delay-once"
        data = _seed(database_url)
        delayed_path = (
            f"/api/v1/trace/report/{data['report_id']}/graph/snapshots/"
            f"{data['snapshot_a']}/proof-packet"
        )
        module = temp / "prompt14_api.py"
        module.write_text(
            """from app.main import app
from app.api import access_dependencies
from app.api.v1 import access as access_api
from tests.helpers.access import TestSessionContext, access_context
app.dependency_overrides[access_dependencies.get_access_context] = lambda: access_context(signed=True)
app.dependency_overrides[access_api.get_access_session_context] = lambda: TestSessionContext()
access_dependencies.REQUEST_SIGNATURE_VERIFIER = lambda request, db: access_context(signed=True)
access_dependencies.REVOCATION_CHECKER = lambda context, db: {'allowed': True, 'revoked_targets': []}
import os
import asyncio
from pathlib import Path
ledger = Path(os.environ['P14_REQUEST_LEDGER'])
@app.middleware('http')
async def record_request(request, call_next):
    with ledger.open('a') as target:
        target.write(request.url.path + '\\n')
    flag = Path(os.environ['P14_DELAY_FLAG'])
    if flag.exists() and request.url.path == os.environ['P14_DELAY_PATH']:
        flag.unlink()
        await asyncio.sleep(1.5)
    return await call_next(request)
"""
        )
        private_key = base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip("=")
        env = {
            **os.environ,
            "DATABASE_URL": database_url,
            "PYTHONPATH": str(ROOT),
            "P14_REQUEST_LEDGER": str(ledger),
            "P14_DELAY_FLAG": str(delay_flag),
            "P14_DELAY_PATH": delayed_path,
        }
        frontend_env = {
            **env,
            "BASTION_GENERATED_TRANSPORT_SECURITY_PROFILE": "ephemeral-device-pop-v1",
            "P9_TEST_SESSION_TOKEN": "sess_prompt14_browser",
            "P9_TEST_DEVICE_PRIVATE_KEY": private_key,
            "BB_API_BASE_URL": "http://127.0.0.1:8000",
        }
        with ExitStack() as stack:
            api_log = stack.enter_context((temp / "api.log").open("w"))
            ui_log = stack.enter_context((temp / "ui.log").open("w"))
            api = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "prompt14_api:app", "--app-dir", str(temp),
                 "--host", "127.0.0.1", "--port", "8000"],
                cwd=ROOT,
                env=env,
                stdout=api_log,
                stderr=subprocess.STDOUT,
            )
            ui = subprocess.Popen(
                [reflex_executable, "run"],
                cwd=FRONTEND,
                env=frontend_env,
                stdout=ui_log,
                stderr=subprocess.STDOUT,
            )
            try:
                _wait("http://127.0.0.1:8000/openapi.json")
                _wait("http://127.0.0.1:3001/")
                report_id = data["report_id"]
                route_current = f"http://127.0.0.1:3001/trace/{report_id}/proof-packet"
                route_a = (
                    f"http://127.0.0.1:3001/trace/{report_id}/history/"
                    f"{data['snapshot_a']}/proof-packet"
                )
                route_b = (
                    f"http://127.0.0.1:3001/trace/{report_id}/history/"
                    f"{data['snapshot_b']}/proof-packet"
                )
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 900},
                        permissions=["clipboard-read", "clipboard-write"],
                        accept_downloads=True,
                    )
                    page = context.new_page()
                    scans: list[dict[str, object]] = []

                    page.goto(route_current, wait_until="networkidle")
                    _wait_packet(page, str(data["packet_current"]))
                    scans.append(_axe(page, "current packet"))
                    baseline = _packet_counts(ledger)
                    theme = page.get_by_role("button", name=re.compile("theme", re.I)).first
                    theme_before = theme.inner_text()
                    theme.click()
                    page.wait_for_timeout(300)
                    theme_after = theme.inner_text()
                    assert theme_after != theme_before
                    theme.click()
                    page.wait_for_timeout(300)
                    assert theme.inner_text() == theme_before
                    assert _packet_counts(ledger) == baseline

                    page.goto(route_a, wait_until="networkidle")
                    text_a = _wait_packet(page, str(data["packet_a"]))
                    assert str(data["a_evidence"]) in text_a
                    assert str(data["b_only_evidence"]) not in text_a
                    scans.append(_axe(page, "historical packet A"))
                    historical_theme = _packet_counts(ledger)
                    theme = page.get_by_role("button", name=re.compile("theme", re.I)).first
                    historical_theme_before = theme.inner_text()
                    theme.click()
                    page.wait_for_timeout(300)
                    assert theme.inner_text() != historical_theme_before
                    assert _packet_counts(ledger) == historical_theme

                    page.goto(route_b, wait_until="networkidle")
                    text_b = _wait_packet(page, str(data["packet_b"]))
                    assert str(data["b_only_evidence"]) in text_b
                    b_evidence_button = page.get_by_role(
                        "button",
                        name=f"Inspect evidence {data['b_only_evidence']}",
                    )
                    b_evidence_button.click()
                    lineage_button = page.get_by_role("button", name="Load lineage")
                    lineage_button.focus()
                    page.keyboard.press("Enter")
                    page.get_by_role("heading", name="Structured Evidence lineage").wait_for()
                    b_lineage = page.get_by_role("dialog", name="Evidence details").inner_text()
                    assert str(data["snapshot_b"]) in b_lineage
                    assert str(data["b_only_evidence"]) in b_lineage
                    page.go_back(wait_until="networkidle")
                    restored = _wait_packet(page, str(data["packet_a"]))
                    assert str(data["b_only_evidence"]) not in restored
                    page.go_forward(wait_until="networkidle")
                    forwarded = _wait_packet(page, str(data["packet_b"]))
                    assert str(data["b_only_evidence"]) in forwarded
                    page.go_back(wait_until="networkidle")
                    restored_again = _wait_packet(page, str(data["packet_a"]))
                    assert str(data["b_only_evidence"]) not in restored_again

                    page.reload(wait_until="networkidle")
                    refreshed = _wait_packet(page, str(data["packet_a"]))
                    assert str(data["snapshot_a"]) in page.url
                    assert str(data["b_only_evidence"]) not in refreshed
                    assert not any(
                        path.endswith(f"/report/{report_id}/proof-packet")
                        for path in _packet_counts(ledger)
                        if path != f"/api/v1/trace/report/{report_id}/proof-packet"
                    )

                    evidence_button = page.get_by_role(
                        "button", name=re.compile("^Inspect evidence")
                    ).first
                    evidence_button.focus()
                    page.keyboard.press("Enter")
                    dialog = page.get_by_role("dialog", name="Evidence details")
                    dialog.wait_for()
                    evidence_trigger_id = evidence_button.get_attribute("id")
                    assert evidence_trigger_id is not None
                    selected_evidence_id = evidence_trigger_id.removeprefix("evidence-trigger-")
                    page.get_by_role("button", name="Load lineage").focus()
                    page.keyboard.press("Enter")
                    page.get_by_role("heading", name="Structured Evidence lineage").wait_for()
                    lineage_text = dialog.inner_text()
                    assert selected_evidence_id in lineage_text
                    assert str(data["snapshot_a"]) in lineage_text
                    assert "produced from" in lineage_text
                    assert "supports" in lineage_text

                    page.get_by_role("button", name="Run deterministic replay").focus()
                    page.keyboard.press("Enter")
                    page.get_by_role("heading", name="Replay result").wait_for()
                    assert "Replay status: match" in dialog.inner_text()
                    assert str(data["snapshot_a"]) in dialog.inner_text()

                    page.get_by_role(
                        "button", name="Verify Evidence identity integrity"
                    ).focus()
                    page.keyboard.press("Enter")
                    page.get_by_role("heading", name="Scoped verification result").wait_for()
                    verification_text = dialog.inner_text()
                    assert "Scope: evidence_identity_integrity" in verification_text
                    assert "Status: verified" in verification_text

                    page.get_by_role("button", name="Copy full safe Evidence ID").focus()
                    page.keyboard.press("Enter")
                    page.get_by_text("Safe Evidence ID copied.", exact=True).wait_for()
                    assert page.evaluate("navigator.clipboard.readText()") == selected_evidence_id

                    with page.expect_download() as download_info:
                        page.get_by_role("button", name="Export safe JSON").focus()
                        page.keyboard.press("Enter")
                    download = download_info.value
                    export_path = temp / "prompt15-export.json"
                    download.save_as(export_path)
                    exported = export_path.read_text()
                    assert selected_evidence_id in exported
                    assert str(data["snapshot_a"]) in exported
                    assert LINEAGE_CANARY not in exported
                    assert CANARY not in exported
                    page.get_by_role("heading", name="Safe export ready").wait_for()
                    workflow_before_theme = _workflow_counts(ledger)
                    theme = page.get_by_role("button", name=re.compile("theme", re.I)).first
                    theme.click()
                    page.wait_for_timeout(300)
                    assert _workflow_counts(ledger) == workflow_before_theme
                    scans.append(_axe(page, "Evidence detail"))
                    page.get_by_role("button", name="Close evidence details").focus()
                    page.keyboard.press("Enter")
                    dialog.wait_for(state="hidden")
                    assert evidence_button.evaluate("element => element === document.activeElement")

                    # Delay A at the API boundary, then switch to B before A returns.
                    # The existing generation/snapshot guard must keep late A out of B State.
                    a_before_delay = _packet_counts(ledger)[delayed_path]
                    delay_flag.touch()
                    page.goto(route_a, wait_until="commit")
                    deadline = time.monotonic() + 5
                    while _packet_counts(ledger)[delayed_path] == a_before_delay:
                        if time.monotonic() >= deadline:
                            raise AssertionError("delayed A request did not start")
                        page.wait_for_timeout(50)
                    page.goto(route_b, wait_until="networkidle")
                    delayed_switch = _wait_packet(page, str(data["packet_b"]))
                    page.wait_for_timeout(1_750)
                    assert str(data["b_only_evidence"]) in delayed_switch
                    assert str(data["packet_b"]) in _body(page)

                    mobile = browser.new_page(
                        viewport={"width": 390, "height": 844},
                        color_scheme="dark",
                        reduced_motion="reduce",
                    )
                    mobile.goto(route_a, wait_until="networkidle")
                    mobile_text = _wait_packet(mobile, str(data["packet_a"]))
                    assert "Verification: not verified" in mobile_text
                    assert "Limitations" in mobile_text
                    mobile.get_by_role("button", name=re.compile("^Inspect evidence")).first.click()
                    mobile.get_by_role("button", name="Load lineage").click()
                    mobile.get_by_role("heading", name="Structured Evidence lineage").wait_for()
                    assert str(data["snapshot_a"]) in mobile.get_by_role(
                        "dialog", name="Evidence details"
                    ).inner_text()
                    scans.append(_axe(mobile, "mobile Evidence lineage"))
                    mobile.screenshot(path=temp / "prompt14-mobile-proof.png", full_page=True)

                    html = page.content() + mobile.content()
                    assert CANARY not in html
                    assert LINEAGE_CANARY not in html
                    browser.close()

                counts = _packet_counts(ledger)
                current_path = f"/api/v1/trace/report/{report_id}/proof-packet"
                a_path = (
                    f"/api/v1/trace/report/{report_id}/graph/snapshots/"
                    f"{data['snapshot_a']}/proof-packet"
                )
                b_path = (
                    f"/api/v1/trace/report/{report_id}/graph/snapshots/"
                    f"{data['snapshot_b']}/proof-packet"
                )
                assert counts[current_path] == 1
                assert counts[b_path] == 3
                # A: initial, two Back navigations, refresh, delayed stale request, and mobile.
                assert counts[a_path] == 6
                workflow_counts = _workflow_counts(ledger)
                assert len(workflow_counts) == 5
                assert sum(
                    count for path, count in workflow_counts.items() if path.endswith("/lineage")
                ) == 3
                assert all(
                    count == 1 for path, count in workflow_counts.items()
                    if not path.endswith("/lineage")
                )
                safe_a = urlopen(f"http://127.0.0.1:8000{a_path}", timeout=5).read().decode()
                assert CANARY not in safe_a
                assert LINEAGE_CANARY not in safe_a
                print(json.dumps({"dataset": data, "packet_request_ledger": counts,
                                  "workflow_request_ledger": workflow_counts,
                                  "axe_scans": scans, "privacy_canary_occurrences": 0,
                                  "unexpected_duplicates": 0}, default=dict, indent=2))
            finally:
                for process in (ui, api):
                    process.terminate()
                for process in (ui, api):
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()


if __name__ == "__main__":
    main()
