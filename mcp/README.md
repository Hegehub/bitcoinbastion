# Bitcoin Bastion MCP Connector

Developer-preview MCP connector for safe AI-agent access to Bitcoin Bastion.

Bitcoin Bastion MCP is no-custody: never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace outputs are advisory-only, not legal verification, and not Bitcoin consensus proof. Market context is not financial advice.

## Install

```bash
cd mcp
python -m pip install -e '.[dev]'
```

## Run

```bash
cd mcp
python -m bastion_mcp.server
```

The baseline server exposes a safe tool registry and a JSON-lines local invocation loop. Production MCP host compatibility testing, auth hardening, and rate-limit evidence remain pending.
