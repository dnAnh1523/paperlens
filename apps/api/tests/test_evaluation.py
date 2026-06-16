import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.evaluation.eval_runner import (
    EvalCase,
    EvaluationComparisonReport,
    EvaluationReport,
    ModeComparisonResult,
    RetrievedEvidence,
    compute_summary,
    evaluate_case,
    evidence_matches_case,
    format_markdown_report,
    load_dataset,
    report_artifact_to_dict,
)


def _evidence(
    *,
    rank: int,
    filename: str = "sample_retrieval_source.txt",
    text: str = "PaperLens uses SQLite for metadata and local folders for artifacts.",
) -> RetrievedEvidence:
    return RetrievedEvidence(
        rank=rank,
        score=3.0,
        backend="like",
        document_id="document-1",
        document_title="sample_retrieval_source",
        document_filename=filename,
        chunk_id=f"chunk-{rank}",
        chunk_index=rank - 1,
        chunk_text=text,
    )


def test_load_dataset_supports_expected_terms_and_answer_terms(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "name": "unit_eval",
                "default_k": 3,
                "cases": [
                    {
                        "id": "storage",
                        "question": "What stores metadata?",
                        "expected_terms": ["SQLite"],
                        "expected_document_filename": "sample_retrieval_source.txt",
                        "scoped_document_filename": "sample_retrieval_source.txt",
                        "difficulty": "easy",
                        "evidence_type": "method",
                    },
                    {
                        "id": "preview",
                        "question": "What can source preview inspect?",
                        "expected_answer_terms": ["selected retrieved chunk"],
                        "expected_chunk_text_contains": "selected retrieved chunk",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    dataset = load_dataset(dataset_path)

    assert dataset.name == "unit_eval"
    assert dataset.default_k == 3
    assert dataset.cases[0].expected_terms == ["SQLite"]
    assert dataset.cases[0].scoped_document_filename == "sample_retrieval_source.txt"
    assert dataset.cases[0].difficulty == "easy"
    assert dataset.cases[0].evidence_type == "method"
    assert dataset.cases[1].expected_answer_terms == ["selected retrieved chunk"]
    assert dataset.cases[1].expected_chunk_text_contains == ["selected retrieved chunk"]


def test_load_dataset_rejects_unknown_difficulty_or_evidence_type(tmp_path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "name": "unit_eval",
                "default_k": 3,
                "cases": [
                    {
                        "id": "bad",
                        "question": "What stores metadata?",
                        "expected_terms": ["SQLite"],
                        "difficulty": "trivial",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="difficulty must be one of"):
        load_dataset(dataset_path)

    dataset_path.write_text(
        json.dumps(
            {
                "name": "unit_eval",
                "default_k": 3,
                "cases": [
                    {
                        "id": "bad",
                        "question": "What stores metadata?",
                        "expected_terms": ["SQLite"],
                        "evidence_type": "appendix",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="evidence_type must be one of"):
        load_dataset(dataset_path)


def test_evidence_matching_requires_filename_and_expected_terms() -> None:
    eval_case = EvalCase(
        case_id="storage",
        question="What stores metadata?",
        expected_terms=["SQLite", "local folders"],
        expected_answer_terms=[],
        expected_document_filename="sample_retrieval_source.txt",
    )

    assert evidence_matches_case(_evidence(rank=1), eval_case)
    assert not evidence_matches_case(_evidence(rank=1, filename="other.txt"), eval_case)
    assert not evidence_matches_case(_evidence(rank=1, text="PaperLens uses SQLite only."), eval_case)


def test_evaluate_case_computes_hit_rank_and_reciprocal_rank() -> None:
    eval_case = EvalCase(
        case_id="chunking",
        question="How does chunking work?",
        expected_terms=["character offsets"],
        expected_answer_terms=[],
    )
    retrieved = [
        _evidence(rank=1, text="Unrelated local stack text."),
        _evidence(rank=2, text="Chunking stores character offsets and estimated token counts."),
    ]

    result = evaluate_case(eval_case, retrieved)

    assert result.hit
    assert result.hit_rank == 2
    assert result.reciprocal_rank == 0.5
    assert result.matched_chunk_id == "chunk-2"


def test_compute_summary_counts_hit_at_k_mrr_and_no_results() -> None:
    hit = evaluate_case(
        EvalCase(
            case_id="hit",
            question="What stores metadata?",
            expected_terms=["SQLite"],
            expected_answer_terms=[],
        ),
        [_evidence(rank=1)],
    )
    miss = evaluate_case(
        EvalCase(
            case_id="miss",
            question="What is missing?",
            expected_terms=["nonexistent"],
            expected_answer_terms=[],
        ),
        [],
    )

    summary = compute_summary(
        "unit_eval",
        [hit, miss],
        k=5,
        retrieval_mode="like",
        retrieval_backend="like",
        fts5_available=False,
    )

    assert summary.total_cases == 2
    assert summary.retrieval_mode == "like"
    assert summary.retrieval_backend == "like"
    assert summary.fts5_available is False
    assert summary.hits == 1
    assert summary.hit_at_k == 0.5
    assert summary.mean_reciprocal_rank == 0.5
    assert summary.no_result_queries == 1


def test_report_artifact_dict_includes_metadata_for_later_plotting() -> None:
    result = evaluate_case(
        EvalCase(
            case_id="storage",
            question="What stores metadata?",
            expected_terms=["SQLite"],
            expected_answer_terms=[],
            difficulty="easy",
            evidence_type="method",
        ),
        [_evidence(rank=1)],
    )
    report = EvaluationReport(
        summary=compute_summary(
            "unit_eval",
            [result],
            k=5,
            retrieval_mode="like",
            retrieval_backend="like",
            fts5_available=True,
        ),
        results=[result],
    )
    generated_at = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)

    payload = report_artifact_to_dict(
        report,
        dataset_path="evals/datasets/unit.json",
        generated_at=generated_at,
    )

    assert payload["generated_at"] == generated_at.isoformat()
    assert payload["dataset_path"] == "evals/datasets/unit.json"
    assert payload["report_kind"] == "single"
    assert payload["report"]["summary"]["retrieval_mode"] == "like"
    assert payload["report"]["results"][0]["difficulty"] == "easy"
    assert payload["report"]["results"][0]["evidence_type"] == "method"


def test_markdown_report_includes_metrics_questions_notes_and_limits() -> None:
    result = evaluate_case(
        EvalCase(
            case_id="storage",
            question="What stores metadata?",
            expected_terms=["SQLite"],
            expected_answer_terms=[],
            difficulty="easy",
            evidence_type="method",
        ),
        [_evidence(rank=1)],
    )
    like_report = EvaluationReport(
        summary=compute_summary(
            "unit_compare",
            [result],
            k=5,
            retrieval_mode="like",
            retrieval_backend="like",
            fts5_available=False,
        ),
        results=[result],
    )
    comparison = EvaluationComparisonReport(
        dataset_name="unit_compare",
        k=5,
        total_cases=1,
        fts5_available=False,
        modes=[
            ModeComparisonResult(
                mode="like",
                available=True,
                backend="like",
                report=like_report,
            ),
            ModeComparisonResult(
                mode="fts5",
                available=False,
                backend=None,
                error="SQLite FTS5 is not available in this environment.",
            ),
        ],
    )

    markdown = format_markdown_report(
        comparison,
        dataset_path="evals/datasets/unit.json",
        generated_at=datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc),
    )

    assert "# Retrieval Evaluation Report: unit_compare" in markdown
    assert "## Run Metadata" in markdown
    assert "## Metrics" in markdown
    assert "| like | like | 1.000 | 1.000 | 0 | yes |" in markdown
    assert "| fts5 |  |  |  |  | no |" in markdown
    assert "## Per-Question Results" in markdown
    assert "| storage | global | easy | method | HIT rank 1 | unavailable | What stores metadata? |" in markdown
    assert "## Interpretation Notes" in markdown
    assert "## Limitations" in markdown


def test_eval_runs_output_directory_is_gitignored() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

    assert "evals/runs/" in gitignore
