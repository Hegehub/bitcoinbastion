# News Scoring Engine

The News Scoring Engine is deterministic, replayable, and Bitcoin-first.

- Correlation is not proof of causation.
- This analysis is informational and evidence-based, not financial advice.
- Scores include factor breakdowns, explanation, provider confidence, and limitations.

## Prompt 15 foundation
- Added rule-based local sentiment and scoring service (`app/services/news_scoring`).
- Added `news_article_scores` model and migration with explainability and limitations fields.

## Production scoring updates
- Added narrative tagging, confidence degradation paths, and provider-aware explainability.
- Correlation is not proof of causation. Scores are informational and evidence-based.
