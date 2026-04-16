from app.services.script.descriptor_awareness_service import DescriptorAwarenessService
from app.services.script.script_analyzer_service import ScriptAnalyzerService


def test_script_analyzer_classifies_taproot_hint() -> None:
    out = ScriptAnalyzerService().analyze(script_hint="tr(multi_a(...))")

    assert out.script_type == "taproot"
    assert out.complexity_score <= 0.5


def test_descriptor_awareness_detects_missing_artifacts() -> None:
    out = DescriptorAwarenessService().evaluate(
        has_descriptor=False,
        has_recovery_instructions=False,
        has_backup_reference=True,
    )

    assert out.completeness_score < 0.6
    assert out.recoverability_assumption == "weak"
    assert out.warnings
