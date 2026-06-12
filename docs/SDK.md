# SDKs

## Python SDK

The Python SDK lives in `sdk/python` and is currently a developer preview. It provides `BastionClient` and `AsyncBastionClient` for existing Bitcoin Bastion API endpoints plus webhook signature verification and WebSocket subscription helpers.

Bitcoin Bastion is no-custody. Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace is advisory-only, not legal verification, and not Bitcoin consensus proof. Market intelligence is not financial advice.

Run SDK checks with:

```bash
make sdk-python-check
```
