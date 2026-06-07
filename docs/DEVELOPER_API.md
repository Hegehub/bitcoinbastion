# Developer API Baseline

Bitcoin Bastion's developer/API layer is currently an internal foundation. The event publisher writes validated domain events into the durable Event Outbox so future webhook, WebSocket, SDK, CLI, MCP, and plugin prompts can consume one shared contract.

## Current state

- Internal event taxonomy and registry are implemented.
- Event Outbox persistence is implemented.
- The internal event publisher records outbox rows for selected domain workflows.
- External webhook delivery is not implemented yet.
- WebSocket streaming is not implemented yet.
- SDK, CLI, MCP connector, and plugin runtime consumption are not implemented yet.

## Safety posture

Event publication is no-custody and advisory-only. Payloads must not contain wallet secrets, credentials, authorization headers, provider credentials, or signing inputs. Event publication is not proof of payment, legal status, Bitcoin consensus proof, or trading signal correctness.

## Example

```python
publish_event(
    "signal.published",
    {"signal_id": 123, "limitations": ["not_financial_advice"]},
    aggregate_type="signal",
    aggregate_id=123,
    source="signal_governance",
)
```

This records a pending internal outbox row only. A later dispatcher prompt will define external delivery.
