# Market Intelligence Foundation

Bitcoin-first, no-custody, evidence-first subsystem foundation for market intelligence.

## Architecture overview
- Domain enums/constants
- Validation + hashing utilities
- SQLAlchemy entity models
- Migration for foundational event table
- Service/repository skeletons
- API router skeleton

## Domain entities
- news_sources
- source_health_records
- source_reputation_profiles
- news_articles
- news_events

## Service responsibilities
- Source lifecycle management
- Article ingest lifecycle (without fetch logic)
- Event lifecycle and grouping (without attribution)
- Source health and reputation scoring scaffolding

## No-custody statement
This subsystem does not custody funds, sign transactions, or execute trades.

## Evidence-first philosophy
All future scoring/attribution must remain explainable and replayable.

## Roadmap placeholders
- Provider adapters
- Dedup clustering
- Sentiment and attribution engine
- Timeline UI and operator workflows
