# Bitcoin Bastion CLI

The `bastion` CLI is an operator-safe, read-first command-line interface over the Python SDK and the existing Bitcoin Bastion API.

Bitcoin Bastion is no-custody. Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace outputs are advisory-only. Trace is not legal verification. Trace is not Bitcoin consensus proof. Market intelligence is not financial advice.

## Installation

Install the repository in editable mode so the `bastion` console script and SDK are available:

```bash
python -m pip install -e '.[dev]'
cd sdk/python && python -m pip install -e '.[dev]'
```

## Configuration

Environment variables:

```text
BB_API_BASE_URL=http://localhost:8000
BB_API_TOKEN=<optional bearer token>
BB_REQUEST_TIMEOUT_SECONDS=5
BB_CLI_OUTPUT=table
```

Global flags:

```bash
bastion --api-base-url http://localhost:8000 --timeout 10 --output json health
bastion --token "$BB_API_TOKEN" status
```

Do not paste API tokens into logs or shared shell history. The CLI redacts token, authorization, signature, and secret-shaped fields in output.

## Output modes

- `table`: human-readable Rich tables.
- `json`: machine-readable JSON.
- `yaml`: currently emits JSON-compatible YAML without adding another dependency.

Python tracebacks are hidden by default. Use `--debug` only for local diagnostics; secrets are still redacted from normalized output.

## Commands

```bash
bastion health
bastion status
bastion signals latest
bastion signals top
bastion signals get <signal_id>
bastion news latest
bastion trace address <bitcoin_address>
bastion trace report <report_id>
bastion trace summary <report_id>
bastion trace evidence <report_id>
bastion evidence packet <packet_id>
bastion market dashboard
bastion market timeline
bastion onchain events
bastion onchain state
bastion treasury requests
bastion treasury pending-approvals
bastion provider-health
bastion webhooks list
bastion webhooks get <webhook_id>
bastion webhooks deliveries <webhook_id>
bastion webhooks test <webhook_id> --yes
bastion ws events --topics signals,trace,market --duration 30 --max-events 20
```

## Trace safety

Trace commands accept public Bitcoin addresses only. They reject seed phrases, mnemonics, private keys, xprv/yprv/zprv, wallet files, keystore material, and signing material before making an API request.

Trace output remains advisory-only and must not be treated as legal verification or Bitcoin consensus proof.

## Treasury limitation

Treasury commands are read-only in this prompt. The CLI can list requests and pending approvals, but it cannot approve, reject, sign, broadcast, or execute treasury actions.

## Webhook test warning

`bastion webhooks test <webhook_id>` requires confirmation unless `--yes` is passed. The command creates a signed test delivery through the API and may result in a test request to the configured endpoint when dispatch is enabled. Webhook secrets and signature secrets are redacted from output.

## WebSocket smoke usage

```bash
bastion ws events --topics signals,trace --duration 15 --max-events 5 --output json
```

Use `--follow` only when you intentionally want the stream to remain open until interrupted.

## Troubleshooting

- `API unavailable`: check `BB_API_BASE_URL` and API process availability.
- `Authentication failed`: check `BB_API_TOKEN` and permissions.
- `Request timed out`: increase `--timeout` or inspect provider/backend health.
- `Invalid input`: review command arguments and make sure no sensitive wallet material was provided.
