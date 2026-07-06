from app.services.events.websocket_filters import SPECIALIZED_STREAMS, stream_event_types


def test_specialized_websocket_stream_contracts_are_declared() -> None:
    required = {
        "signals",
        "news",
        "onchain",
        "market",
        "trace",
        "treasury",
        "provider-health",
        "intelligence-timeline",
    }
    assert required <= set(SPECIALIZED_STREAMS)
    for stream in required:
        assert stream_event_types(stream)
