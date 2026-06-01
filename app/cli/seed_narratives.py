from app.db.session import SessionLocal
from app.services.intelligence.narrative_heatmap import NarrativeClassificationService


def main() -> None:
    with SessionLocal() as db:
        narratives = NarrativeClassificationService(db).ensure_narratives()
        db.commit()
        print(f"seeded narratives={len(narratives)}")


if __name__ == "__main__":
    main()
