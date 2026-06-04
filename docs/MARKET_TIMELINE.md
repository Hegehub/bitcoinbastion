# Market Timeline

The Market Timeline is the paginated, replay-safe chronology for Bastion Market Time Machine. It turns isolated records into a single market-memory stream that can be rendered in the web dashboard and consumed by API clients.

## Architecture

```text
News / Candles / Signals / Reviews / Evidence
    ↓
IntelligenceTimelineEvent
    ↓
Paginated timeline DTO
    ↓
/market + /intelligence/timeline + /api/v1/intelligence/timeline
```

The timeline service never calculates causation. It renders backend DTO fields and keeps uncertainty visible.

## Routes

- `GET /market` renders the primary Market Timeline and Candlestick Intelligence Dashboard.
- `GET /intelligence/timeline` renders the HTML timeline with filters, sorting, pagination, and window selection.
- `GET /api/v1/intelligence/timeline` returns the API timeline contract.
- `GET /api/v1/intelligence/timeline/day` returns a 24-hour paginated timeline DTO.
- `GET /api/v1/intelligence/timeline/hour` returns a 1-hour paginated timeline DTO.
- `GET /api/v1/intelligence/events/{event_id}/timeline` returns event context, chart markers, and related timeline items.

## Performance

The timeline is designed for large datasets by using bounded requests:

- timeline pages are capped at 100 items;
- candle and marker DTOs support lazy loading and bounded limits up to 10,000 rows;
- filtering is applied before pagination where possible;
- clients should request additional pages instead of full-table exports.

This supports operational targets of 10,000 candles, 5,000 events, and 10,000 markers without forcing a full-table scan in the UI.

## Filters

Supported filter labels include:

- `positive`
- `negative`
- `security`
- `regulatory`
- `institutional`
- `mining`
- `lightning`
- `macro`
- `high_confidence`
- `operator_reviewed`

Filters are combinable with comma-separated values, for example `news,high_confidence`.

## Safety

Every timeline response and panel must preserve:

- `correlation_not_causation`
- `evidence_based`
- `operator_reviewed`
- `confidence_score`

The timeline is historical and evidentiary. It must not guarantee causation, hide uncertainty, hide missing evidence, hide degraded providers, or present speculation as fact.
