from app.schemas.education import EducationSnippetOut


class EducationService:
    def list_snippets(self) -> list[EducationSnippetOut]:
        return [
            EducationSnippetOut(
                slug="utxo-basics",
                title="UTXO Basics for Treasury Teams",
                summary="How UTXO composition impacts privacy, fees, and spend reliability.",
                level="beginner",
            ),
            EducationSnippetOut(
                slug="fee-market-regimes",
                title="Understanding Fee Market Regimes",
                summary="How to interpret mempool pressure and choose a confirmation strategy.",
                level="intermediate",
            ),
        ]
