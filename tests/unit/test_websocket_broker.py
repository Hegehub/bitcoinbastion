import asyncio

from app.services.events.websocket_broker import WebSocketBroker
from app.services.events.websocket_serialization import heartbeat_message


class FakeWebSocket:
    def __init__(self, *, fail_send: bool = False) -> None:
        self.accepted = False
        self.messages: list[dict[str, object]] = []
        self.fail_send = fail_send

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict[str, object]) -> None:
        if self.fail_send:
            raise RuntimeError("send failed")
        self.messages.append(data)


def test_connection_can_be_registered_and_removed() -> None:
    async def run() -> None:
        broker = WebSocketBroker()
        websocket = FakeWebSocket()

        connection_id = await broker.connect(websocket, {"signals"})

        assert websocket.accepted is True
        assert broker.active_connection_count() == 1
        await broker.disconnect(connection_id)
        assert broker.active_connection_count() == 0

    asyncio.run(run())


def test_event_sent_only_to_matching_topic_subscribers() -> None:
    async def run() -> None:
        broker = WebSocketBroker()
        signals = FakeWebSocket()
        trace = FakeWebSocket()
        await broker.connect(signals, {"signals"})
        await broker.connect(trace, {"trace"})

        await broker.broadcast_event({"type": "event", "event_type": "signal.created"})

        assert len(signals.messages) == 1
        assert trace.messages == []

    asyncio.run(run())


def test_event_type_allowlist_filters_specialized_subscribers() -> None:
    async def run() -> None:
        broker = WebSocketBroker()
        signals = FakeWebSocket()
        await broker.connect(signals, {"signals"}, event_types={"signal.published"})

        await broker.broadcast_event({"type": "event", "event_type": "signal.created"})
        await broker.broadcast_event({"type": "event", "event_type": "signal.published"})

        assert [message["event_type"] for message in signals.messages] == ["signal.published"]

    asyncio.run(run())


def test_send_failure_cleans_up_connection() -> None:
    async def run() -> None:
        broker = WebSocketBroker()
        websocket = FakeWebSocket(fail_send=True)
        await broker.connect(websocket, {"signals"})

        await broker.broadcast_event({"type": "event", "event_type": "signal.created"})

        assert broker.active_connection_count() == 0

    asyncio.run(run())


def test_send_heartbeat() -> None:
    async def run() -> None:
        broker = WebSocketBroker()
        websocket = FakeWebSocket()
        connection_id = await broker.connect(websocket, {"signals"})

        await broker.send_heartbeat(connection_id)

        assert websocket.messages[0]["type"] == "heartbeat"
        assert heartbeat_message()["event_type"] == "heartbeat"

    asyncio.run(run())
