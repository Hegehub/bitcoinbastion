# Intelligence API

The intelligence API exposes Market Time Machine evidence layers for candle attribution, historical similarity, and market memory.

## Historical Similarity and Market Memory

- `GET /api/v1/intelligence/events/{event_id}/similar` returns similar historical events, pattern reasoning, reaction statistics, confidence, and limitations.
- `GET /api/v1/intelligence/events/{event_id}/memory` returns the event's pattern matches, persisted similar events, confidence history, and limitations.
- `GET /api/v1/intelligence/patterns` returns the active production market-pattern catalog.
- `GET /api/v1/intelligence/patterns/{pattern_id}` returns a single pattern by numeric ID or slug.
- `GET /api/v1/intelligence/patterns/{pattern_id}/history` returns historical events classified under a pattern.
- `GET /api/v1/intelligence/patterns/{pattern_id}/reaction-profile` returns median and average BTC reaction windows for a pattern.

## Response Guarantees

Historical-similarity responses include the required disclaimer: "Historical similarity does not guarantee future market behavior." They also include correlation/causation limitations and confidence reasoning where available.
