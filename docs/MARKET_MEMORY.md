# Market Memory

Market Memory is the persistence and retrieval layer for historical Bitcoin market context. It supports Market Time Machine, reverse explanation, narrative workflows, and future operator review screens.

## Capabilities

`MarketMemoryService` can:

- seed and retrieve the active pattern catalog
- classify events into ranked patterns
- retrieve similar historical events
- retrieve pattern history
- generate pattern reaction profiles
- retrieve confidence history for an event
- produce an event-memory packet for UI and operator tools

## Evidence Returned

Market-memory responses include pattern matches, historical analogs, confidence history, limitations, and reaction statistics where available.

## Safety Principles

Market Memory is informational. It preserves uncertainty and always avoids future-price claims. Historical similarity does not guarantee future market behavior.
