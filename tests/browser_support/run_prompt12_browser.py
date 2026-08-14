"""Live Prompt-12 Submit → persisted Report browser acceptance."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
sys.path[:0] = [str(ROOT), str(FRONTEND)]
DB = ROOT / "prompt12-browser.db"
ADDRESS = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"


def wait(url: str, timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server unavailable: {url}")


def main() -> None:
    DB.unlink(missing_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
    from app.db import models as _models  # noqa: F401
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(engine)
    env = os.environ | {
        "DATABASE_URL": f"sqlite:///{DB}",
        "PYTHONPATH": f"{FRONTEND}:{ROOT}:{os.environ.get('PYTHONPATH', '')}",
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
            wait("http://127.0.0.1:8000/health")
            wait("http://127.0.0.1:3000/trace")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto("http://127.0.0.1:3000/trace", wait_until="networkidle")
                field = page.get_by_role("textbox", name="Public Bitcoin address")
                field.fill(ADDRESS)
                page.get_by_role("button", name="Submit public Bitcoin address").focus()
                page.keyboard.press("Enter")
                page.wait_for_url("**/trace/*", timeout=30000)
                page.get_by_text(f"Analyzed subject: {ADDRESS}", exact=False).wait_for()
                body = page.locator("body").inner_text()
                assert "Baseline deterministic scoring report." in body
                assert "COMPLETE" in body and "advisory-only" in body
                report_url = page.url
                page.reload(wait_until="networkidle")
                page.get_by_text(f"Analyzed subject: {ADDRESS}", exact=False).wait_for()
                page.go_back(wait_until="networkidle")
                page.go_forward(wait_until="networkidle")
                assert page.url == report_url
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.get_by_text(f"Analyzed subject: {ADDRESS}", exact=False).is_visible()
                page.screenshot(path="/tmp/p12-trace-report.png", full_page=True)
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
        assert log.count('POST /api/v1/trace/submit HTTP/1.1" 201') == 1
        assert log.count('GET /api/v1/trace/report/') >= 2
        assert "Idempotency-Key" not in log
        print("PASS trace_live subject=BITCOIN_ADDRESS processing=T1 submit_requests=1 duplicates=0")
        print("PASS trace_report persisted=true refresh_no_resubmit=true back_forward_no_resubmit=true")
    DB.unlink(missing_ok=True)
    for suffix in ("-wal", "-shm"):
        Path(str(DB) + suffix).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
