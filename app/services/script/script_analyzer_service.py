from app.domain.script import ScriptProfile
from app.schemas.script import ScriptAnalysisOut


class ScriptAnalyzerService:
    def analyze(self, *, script_hint: str) -> ScriptAnalysisOut:
        hint = script_hint.lower().strip()

        if "tr(" in hint or "taproot" in hint or hint.startswith("bc1p"):
            profile = ScriptProfile(script_type="taproot", complexity_score=0.45, risk_level="medium")
            reason = "Detected Taproot-like descriptor/address pattern."
        elif "wsh" in hint or "multi" in hint or hint.startswith("bc1q"):
            profile = ScriptProfile(script_type="p2wsh", complexity_score=0.65, risk_level="medium")
            reason = "Detected witness script hash / multisig pattern."
        elif "sh(" in hint or hint.startswith("3"):
            profile = ScriptProfile(script_type="p2sh", complexity_score=0.72, risk_level="high")
            reason = "Detected P2SH wrapper pattern."
        elif "pkh" in hint or hint.startswith("1"):
            profile = ScriptProfile(script_type="p2pkh", complexity_score=0.55, risk_level="medium")
            reason = "Detected legacy P2PKH pattern."
        else:
            profile = ScriptProfile(script_type="unknown", complexity_score=0.8, risk_level="high")
            reason = "Could not classify script confidently from provided hint."

        return ScriptAnalysisOut(
            script_type=profile.script_type,
            complexity_score=profile.complexity_score,
            risk_level=profile.risk_level,
            confidence=0.7 if profile.script_type != "unknown" else 0.4,
            freshness={"source": "script_hint", "state": "evaluated"},
            explainability={"hint": script_hint, "reason": reason},
        )
