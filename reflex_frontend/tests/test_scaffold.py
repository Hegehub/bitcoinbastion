from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_required_scaffold_files_exist() -> None:
    required = [
        "rxconfig.py",
        "bastion_ui/app.py",
        "pyproject.toml",
        ".env.example",
        "Dockerfile",
        "bastion_ui/routes/home.py",
        "bastion_ui/components/layout/public_layout.py",
        "bastion_ui/services/api_client.py",
        "bastion_ui/theme/tokens.py",
        "bastion_ui/theme/styles.py",
        "bastion_ui/security/forbidden_inputs.py",
        "bastion_ui/security/safety_copy.py",
    ]
    for relative in required:
        assert (ROOT / relative).exists(), relative


def test_readme_documents_experimental_boundaries() -> None:
    readme = read("README.md")
    assert "experimental Python-first Reflex frontend shell" in readme
    assert "Reflex does not replace Next.js yet" in readme
    assert "FastAPI remains the source of truth" in readme
    assert "/market` remains owned by the existing FastAPI/Jinja Market Time Machine dashboard" in readme


def test_rxconfig_uses_parallel_ports() -> None:
    config = read("rxconfig.py")
    assert "frontend_port=3001" in config
    assert "backend_port=8001" in config


def test_home_page_contains_required_positioning_copy() -> None:
    home = read("bastion_ui/routes/home.py")
    required_copy = [
        "Experimental Reflex frontend shell.",
        "FastAPI remains the source of truth.",
        "Next.js remains available until route and API parity are proven.",
        "No custody.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
        "Advisory-only.",
    ]
    for copy in required_copy:
        assert copy in home
