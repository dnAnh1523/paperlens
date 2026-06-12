from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _configure_api_imports() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    api_root = repo_root / "apps" / "api"
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    sqlite_path = api_root / "data" / "sqlite" / "paperlens.db"
    storage_path = api_root / "data" / "storage"
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{sqlite_path.as_posix()}")
    os.environ.setdefault("LOCAL_STORAGE_ROOT", str(storage_path))
    return repo_root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed a local retrieval evaluation fixture into PaperLens SQLite/storage state.",
    )
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to a local fixture document to store, ingest, and chunk.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete matching seeded fixture documents before creating a fresh document.",
    )
    return parser.parse_args()


def _resolve_fixture_path(repo_root: Path, fixture: str) -> Path:
    fixture_path = Path(fixture)
    if fixture_path.is_absolute():
        return fixture_path
    return repo_root / fixture_path


def main() -> int:
    repo_root = _configure_api_imports()

    from app.db.session import SessionLocal, init_db
    from app.evaluation.fixture_seeder import EvalFixtureSeedError, seed_eval_fixture

    args = _parse_args()
    fixture_path = _resolve_fixture_path(repo_root, args.fixture)

    init_db()
    try:
        with SessionLocal() as db:
            result = seed_eval_fixture(db, fixture_path, reset=args.reset)
    except (EvalFixtureSeedError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print("Seeded retrieval eval fixture")
    print(f"Fixture: {fixture_path}")
    print(f"Document id: {result.document_id}")
    print(f"Original filename: {result.original_filename}")
    print(f"Storage path: {result.storage_path}")
    print(f"Created new document: {result.created}")
    print(f"Reset requested: {result.reset}")
    print(f"Ingestion status: {result.ingestion_status}")
    print(f"Chunk count: {result.chunk_count}")
    print("")
    print(
        "Next: python scripts/run_retrieval_eval.py --dataset "
        "evals/datasets/sample_retrieval_smoke.json --compare-modes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
