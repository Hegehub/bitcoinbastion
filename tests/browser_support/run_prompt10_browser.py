"""Real-stack Prompt-10 typed history browser acceptance."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
DB = ROOT / "prompt10-browser.db"


def wait(url: str) -> None:
    for _ in range(360):
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError(f"server unavailable: {url}")


def seed() -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
    from app.db import models as _models  # noqa: F401
    from app.db.base import Base
    from app.db.models.candle_attribution import CandleAttribution
    from app.db.models.evidence_packet import EvidencePacket
    from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
    from app.db.models.market_narrative import MarketNarrative
    from app.db.models.news_source import NewsSource
    from app.db.session import SessionLocal, engine

    Base.metadata.create_all(engine)
    now = datetime(2026, 8, 12, 12)
    db = SessionLocal()
    db.add(
        IntelligenceTimelineEvent(
            id=101,
            event_type="news_event",
            source_kind="NEWS",
            title="ETF filing observed",
        summary="Backend-stored observation; temporal proximity is not causality.",
        event_time=now,
        ingested_at=now,
        updated_at=now,
        related_event_id=101,
        )
    )
    db.add(
        CandleAttribution(
            id=201,
            candle_id=1,
            timeframe="1h",
            candle_open_time=now,
            candle_close_time=now,
            attribution_type="correlation_candidate",
            confidence_score=0.61,
            summary_text="Backend correlation candidate.",
            limitations_json={"causality": "This relationship is not a causal finding."},
        )
    )
    db.add(
        MarketNarrative(
            id=301,
            slug="etf-flow",
            name="ETF flow",
            display_name="ETF flow narrative",
            description="Stored backend narrative without generated causal wording.",
            avg_confidence=0.52,
            updated_at=now,
        )
    )
    db.add(
        NewsSource(
            id=401,
            uuid="source-safe-401",
            name="Example Market Source",
            kind="rss",
            category="market_media",
            homepage_url="https://example.com/market",
            is_public=True,
            metadata_json={"api_key": "never-render"},
            last_success_at=now,
        )
    )
    db.add(
        EvidencePacket(
            id=501,
            packet_type="market",
            source_entity_type="news_event",
            source_entity_id=101,
            event_id=101,
            title="Related source packet",
            summary="Reference only.",
            created_at=now,
        )
    )
    db.commit()
    db.close()


def main() -> None:
    seed()
    env = os.environ | {
        "DATABASE_URL": f"sqlite:///{DB}",
        "PYTHONPATH": f"{FRONTEND}:{ROOT}",
    }
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
        ),
    ]
    try:
        wait("http://127.0.0.1:8000/health")
        wait("http://127.0.0.1:3000/market/timeline")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto("http://127.0.0.1:3000/market/timeline", wait_until="networkidle")
            page.get_by_text("ETF filing observed", exact=True).wait_for()
            assert "NEWS" in page.locator(".market-timeline-item").inner_text()
            assert "Related source packet" in page.locator(".market-timeline-item").inner_text()
            page.get_by_role("button", name="Open historical replay for event").click()
            page.locator("#replay-capture-id").wait_for()
            assert "Historical replay" in page.get_by_role("status").all_inner_texts()[-1]
            page.goto("http://127.0.0.1:3000/market/time-machine", wait_until="networkidle")
            page.get_by_text("CORRELATION_CANDIDATE", exact=False).wait_for()
            page.goto("http://127.0.0.1:3000/market/narratives", wait_until="networkidle")
            page.get_by_text("ETF flow narrative", exact=True).wait_for()
            page.goto("http://127.0.0.1:3000/market/sources", wait_until="networkidle")
            page.get_by_text("Example Market Source", exact=True).wait_for()
            assert "never-render" not in page.locator("body").inner_text()
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
                "document.documentElement.clientWidth"
            )
            print("PASS prompt10 timeline/replay/attribution/narrative/source/evidence mobile")
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
        Path(str(DB) + "-wal").unlink(missing_ok=True)
        Path(str(DB) + "-shm").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
