"""Live Reflex A2R acceptance against explicitly started integration services."""

from __future__ import annotations

import os
import sqlite3
from collections import Counter

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright
CANARY = "ACCESS_SECRET_CANARY_NEVER_BROWSER"
PRIVATE_MARKER = "A2R_PRIVATE_KEY_MARKER_NEVER_NETWORK"


def counts(db: sqlite3.Connection) -> Counter[str]:
    return Counter(
        checkout=db.execute("select count(*) from access_checkout_sessions").fetchone()[0],
        challenge=db.execute("select count(*) from access_issuance_challenges").fetchone()[0],
        grant=db.execute("select count(*) from access_issued_grants").fetchone()[0],
    )


def main() -> None:
    frontend = os.getenv("A2R_FRONTEND_URL", "http://127.0.0.1:3001")
    database_path = os.environ["A2R_DATABASE_PATH"]
    network_text: list[str] = []
    with sqlite3.connect(database_path) as db, sync_playwright() as playwright:
        before = counts(db)
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        page.on("request", lambda request: network_text.append(request.post_data or ""))
        page.goto(f"{frontend}/access/plans")
        page.get_by_role("button", name="Select backend Offer basic_pass").focus()
        page.keyboard.press("Enter")
        page.get_by_role("button", name="Create one Checkout").focus()
        page.keyboard.press("Enter")
        page.wait_for_url("**/access/checkout?checkout_id=**")
        checkout_id = page.url.split("checkout_id=", 1)[1]
        after_checkout = counts(db)
        assert after_checkout["checkout"] - before["checkout"] == 1
        payment_id = db.execute(
            "select payment_intent_id from access_checkout_sessions where id = ?", (checkout_id,)
        ).fetchone()[0]
        db.execute("update access_payment_intents set status = 'paid' where id = ?", (payment_id,))
        db.commit()
        page.reload()
        page.get_by_role("button", name="Verify this device key and issue Access once").focus()
        page.keyboard.press("Enter")
        page.wait_for_url("**/access/payment/success?grant_id=**")
        page.get_by_text("Authoritative issued Access").wait_for()
        grant_id = page.url.split("grant_id=", 1)[1]
        after_issue = counts(db)
        assert after_issue["challenge"] - before["challenge"] == 1
        assert after_issue["grant"] - before["grant"] == 1
        grant = db.execute(
            "select id, capability from access_issued_grants where id = ?", (grant_id,)
        ).fetchone()
        assert grant is not None
        body = page.locator("body").inner_text()
        assert grant[0] in body and grant[1] in body
        assert CANARY not in body and PRIVATE_MARKER not in body
        assert CANARY not in page.content() and PRIVATE_MARKER not in page.content()
        assert CANARY not in page.url and PRIVATE_MARKER not in page.url
        assert all(CANARY not in item and PRIVATE_MARKER not in item for item in network_text)
        page.get_by_label("Toggle light and dark theme").first.click()
        assert counts(db) == after_issue
        page.reload()
        page.get_by_text(grant[0]).wait_for()
        assert counts(db) == after_issue
        second = context.new_page()
        second.goto(page.url)
        second.get_by_text(grant[0]).wait_for()
        assert counts(db) == after_issue
        assert second.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        results = Axe().run(second)
        serious = [
            item for item in results.response.get("violations", [])
            if item.get("impact") in {"critical", "serious"}
        ]
        assert not serious, [(item["id"], item.get("impact")) for item in serious]
        print(
            {
                "checkout_mutations": 1,
                "challenge_mutations": 1,
                "issuance_mutations": 1,
                "unexpected_duplicates": 0,
                "grant_id": grant[0],
                "canary_occurrences": 0,
                "private_key_marker_occurrences": 0,
                "serious_accessibility_violations": 0,
            }
        )
        browser.close()


if __name__ == "__main__":
    main()
