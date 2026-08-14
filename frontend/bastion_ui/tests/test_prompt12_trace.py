import asyncio

import httpx

from bastion_ui.domain.prompt12 import adapt_trace_report, adapt_trace_submission
from bastion_ui.transport.foundation import HttpTransport
from bastion_ui.transport.generated_http import (
    SubmitTraceApiV1TraceSubmitPostRequest,
    submit_trace_api_v1_trace_submit_post,
)
from bastion_ui.transport.generated_schemas import TraceSubjectType, TraceSubmitRequest


def test_trace_submission_projection_is_strictly_bounded() -> None:
    model = adapt_trace_submission(
        {
            "trace_id": 7,
            "report_id": 7,
            "status": "COMPLETE",
            "normalized_subject": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
            "idempotency_replayed": False,
            "internal_secret": "must-not-project",
        }
    )
    assert model.report_id == "7"
    assert not hasattr(model, "internal_secret")


def test_report_projection_preserves_backend_truth_without_inference() -> None:
    model = adapt_trace_report(
        {
            "id": 7,
            "address": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
            "chain": "bitcoin",
            "status": "COMPLETE",
            "summary": "Backend-authored advisory summary.",
            "trace_band": "UNKNOWN",
            "trace_score": 0.0,
            "confidence": 0.0,
            "source_quality": "LOW",
            "freshness": "UNKNOWN",
            "limitations": ["Baseline sources only."],
            "evidence_refs": [],
            "created_at": "2026-08-12T12:00:00Z",
            "raw_provider_payload": {"credential": "forbidden"},
        }
    )
    assert model.score == 0.0
    assert model.confidence == 0.0
    assert model.advisory_band == "UNKNOWN"
    assert model.limitations == ("Baseline sources only.",)
    assert not hasattr(model, "raw_provider_payload")


def test_frontend_contains_no_trace_conclusion_recomputation() -> None:
    from pathlib import Path

    root = Path(__file__).parents[1]
    sources = "\n".join(
        (root / path).read_text()
        for path in ("domain/prompt12.py", "state/trace_state.py", "state/trace_report_state.py")
    )
    for forbidden in ("score >=", "confidence +", "confidence -", "trace_score *"):
        assert forbidden not in sources


def test_generated_submit_client_forwards_idempotency_header() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["idempotency"] = request.headers["Idempotency-Key"]
        return httpx.Response(
            201,
            json={
                "success": True,
                "data": {
                    "trace_id": 9,
                    "report_id": 9,
                    "status": "COMPLETE",
                    "normalized_subject": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
                    "network": "bitcoin-mainnet",
                    "idempotency_replayed": False,
                },
            },
        )

    async def run():
        async with httpx.AsyncClient(
            base_url="https://example.test", transport=httpx.MockTransport(handler)
        ) as client:
            return await submit_trace_api_v1_trace_submit_post(
                HttpTransport(client),
                SubmitTraceApiV1TraceSubmitPostRequest(
                    Idempotency_Key="trace-submit-attempt-typed-0001",
                    body=TraceSubmitRequest(
                        subject_type=TraceSubjectType(root="BITCOIN_ADDRESS"),
                        subject="1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
                        network="bitcoin-mainnet",
                    ),
                ),
            )

    response = asyncio.run(run())
    assert response.root.data.report_id == 9
    assert seen["idempotency"] == "trace-submit-attempt-typed-0001"
