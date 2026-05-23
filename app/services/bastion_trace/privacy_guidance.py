from app.schemas.bastion_trace import PrivacyGuidance


def build_privacy_guidance() -> PrivacyGuidance:
    return PrivacyGuidance(items=[
        "UTXO-level privacy assessment is source-limited. Do not infer safety or risk from missing data.",
        "Address reuse may reduce privacy. Prefer fresh receiving addresses when possible.",
        "Dust-like outputs may create privacy exposure. Avoid consolidating unknown dust with high-value UTXOs without review.",
        "Consolidating many UTXOs can link funds together. Consider privacy impact before consolidation.",
        "Possible toxic change is a heuristic signal only. Manual review is recommended before drawing conclusions.",
        "Privacy exposure is not the same as illicit-risk evidence.",
    ])
