from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
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
        description="Run a local PaperLens retrieval evaluation against SQLite chunk state.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to a retrieval evaluation dataset JSON file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Override retrieval depth k. Defaults to dataset default_k.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "like", "fts5"),
        default="auto",
        help="Retrieval mode to evaluate. Auto uses FTS5 when available and falls back to LIKE.",
    )
    parser.add_argument(
        "--compare-modes",
        action="store_true",
        help="Evaluate the dataset under LIKE, FTS5 when available, and AUTO.",
    )
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write the report JSON to evals/runs/.",
    )
    parser.add_argument(
        "--write-markdown",
        action="store_true",
        help="Write a Markdown report to evals/runs/.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional explicit JSON output path. Implies --write-json.",
    )
    parser.add_argument(
        "--markdown-output",
        default=None,
        help="Optional explicit Markdown output path. Implies --write-markdown.",
    )
    return parser.parse_args()


def _default_output_path(
    repo_root: Path,
    dataset_name: str,
    generated_at: datetime,
    suffix: str,
) -> Path:
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    safe_name = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in dataset_name)
    return repo_root / "evals" / "runs" / f"{safe_name}_{timestamp}{suffix}"


def main() -> int:
    repo_root = _configure_api_imports()

    from app.db.session import SessionLocal, init_db
    from app.evaluation.eval_runner import (
        format_comparison_report,
        format_markdown_report,
        format_report,
        load_dataset,
        report_artifact_to_dict,
        run_retrieval_eval,
        run_retrieval_eval_comparison,
    )
    from app.services.retrieval_service import RetrievalBackendUnavailableError

    args = _parse_args()
    dataset = load_dataset(args.dataset)

    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be a positive integer.")

    init_db()
    with SessionLocal() as db:
        if args.compare_modes:
            report = run_retrieval_eval_comparison(db, dataset, limit=args.limit)
            formatted_report = format_comparison_report(report)
            output_dataset_name = f"{dataset.name}_comparison"
        else:
            try:
                report = run_retrieval_eval(db, dataset, limit=args.limit, mode=args.mode)
            except RetrievalBackendUnavailableError as exc:
                raise SystemExit(str(exc)) from exc
            formatted_report = format_report(report)
            output_dataset_name = dataset.name

    print(formatted_report)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0)

    if args.write_json or args.output:
        output_path = (
            Path(args.output)
            if args.output
            else _default_output_path(repo_root, output_dataset_name, generated_at, ".json")
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = report_artifact_to_dict(
            report,
            dataset_path=args.dataset,
            generated_at=generated_at,
        )
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote JSON report: {output_path}")

    if args.write_markdown or args.markdown_output:
        markdown_output_path = (
            Path(args.markdown_output)
            if args.markdown_output
            else _default_output_path(repo_root, output_dataset_name, generated_at, ".md")
        )
        markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_output_path.write_text(
            format_markdown_report(
                report,
                dataset_path=args.dataset,
                generated_at=generated_at,
            ),
            encoding="utf-8",
        )
        print(f"\nWrote Markdown report: {markdown_output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
