from pathlib import Path


def test_new_docs_exist() -> None:
    for p in (
        'docs/TECHNICAL_DEBT.md',
        'docs/PRE_RELEASE_GAPS.md',
        'docs/ENVIRONMENT_VARIABLES.md',
        '.env.example',
    ):
        assert Path(p).exists()


def test_no_false_production_ready_wording() -> None:
    for p in ('README.md', 'docs/STATUS.md', 'docs/PRODUCTION_READINESS.md'):
        text = Path(p).read_text().lower()
        assert 'is production-ready' not in text
        assert 'production ready' not in text


def test_env_example_has_placeholders() -> None:
    text = Path('.env.example').read_text()
    assert 'REPLACE_ME' in text
