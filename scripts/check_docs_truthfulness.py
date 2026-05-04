#!/usr/bin/env python
"""Check documentation drift for T-02 truth fixes.

Checks:
1) docs/API_CONTRACTS.md route inventory vs app/api/v1 routers
2) docs/DOMAIN_MODELS.md model class inventory vs app/db/models/__all__
3) README.md has a single '## Core documentation' section
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

API_DOC = REPO_ROOT / "docs" / "API_CONTRACTS.md"
MODELS_DOC = REPO_ROOT / "docs" / "DOMAIN_MODELS.md"
README_DOC = REPO_ROOT / "README.md"
API_DIR = REPO_ROOT / "app" / "api" / "v1"
MODELS_INIT = REPO_ROOT / "app" / "db" / "models" / "__init__.py"

METHOD_ROUTE_RE = re.compile(r"`(?:GET|POST|PUT|PATCH|DELETE)\s+(/api/v1[^`\s]*)`")
ROUTER_PREFIX_RE = re.compile(r'APIRouter\(prefix="([^"]+)"')
ROUTE_RE = re.compile(r'@router\.(?:get|post|put|delete|patch)\("([^"]*)"')
MODEL_BULLET_RE = re.compile(r"^- `([A-Za-z][A-Za-z0-9_]*)`$", re.MULTILINE)


def collect_code_routes() -> set[str]:
    routes: set[str] = set()
    for api_file in API_DIR.glob("*.py"):
        text = api_file.read_text()
        prefix_match = ROUTER_PREFIX_RE.search(text)
        if not prefix_match:
            continue
        prefix = prefix_match.group(1)
        for match in ROUTE_RE.finditer(text):
            path = match.group(1)
            routes.add(f"/api/v1{prefix}{'' if path == '' else path}")
    return routes


def collect_documented_routes() -> set[str]:
    text = API_DOC.read_text()
    return set(METHOD_ROUTE_RE.findall(text))


def collect_model_exports() -> set[str]:
    tree = ast.parse(MODELS_INIT.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, ast.List):
                return {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)}
    return set()


def collect_documented_models() -> set[str]:
    text = MODELS_DOC.read_text()
    return set(MODEL_BULLET_RE.findall(text))


def check_core_docs_heading() -> list[str]:
    text = README_DOC.read_text()
    hits = len(re.findall(r"^## Core documentation$", text, flags=re.MULTILINE))
    if hits != 1:
        return [f"README core documentation headings expected=1 actual={hits}"]
    return []


def main() -> int:
    errors: list[str] = []

    code_routes = collect_code_routes()
    doc_routes = collect_documented_routes()

    missing_routes = sorted(code_routes - doc_routes)
    extra_routes = sorted(doc_routes - code_routes)

    if missing_routes:
        errors.append(f"API_CONTRACTS missing routes: {', '.join(missing_routes)}")
    if extra_routes:
        errors.append(f"API_CONTRACTS undocumented-in-code routes: {', '.join(extra_routes)}")

    model_exports = collect_model_exports()
    doc_models = collect_documented_models()

    missing_models = sorted(model_exports - doc_models)
    extra_models = sorted(doc_models - model_exports)

    if missing_models:
        errors.append(f"DOMAIN_MODELS missing model exports: {', '.join(missing_models)}")
    if extra_models:
        errors.append(f"DOMAIN_MODELS unknown model names: {', '.join(extra_models)}")

    errors.extend(check_core_docs_heading())

    if errors:
        print("Docs truthfulness check failed:")
        for err in errors:
            print("-", err)
        return 1

    print(
        "Docs truthfulness check passed:",
        f"routes={len(code_routes)}",
        f"models={len(model_exports)}",
        "core_docs_heading=1",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
