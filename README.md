# Bitcoin Bastion

Bitcoin Bastion is a Bitcoin-native intelligence and operations platform.

## MVP capabilities
- RSS news ingestion and deduplication
- Bitcoin relevance scoring
- On-chain event abstraction with rule-based alerts
- Signal generation and API exposure
- Telegram formatting and delivery service abstraction

## Quick start
```bash
make up
make migrate
make test
```

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```
