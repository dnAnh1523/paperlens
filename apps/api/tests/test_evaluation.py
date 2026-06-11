import json

from app.evaluation.eval_runner import (
    EvalCase,
    RetrievedEvidence,
    compute_summary,
    evaluate_case,
    evidence_matches_case,
    load_dataset,
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
    assert dataset.cases[1].expected_answer_terms == ["selected retrieved chunk"]
    assert dataset.cases[1].expected_chunk_text_contains == ["selected retrieved chunk"]


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

    summary = compute_summary("unit_eval", [hit, miss], k=5)

    assert summary.total_cases == 2
    assert summary.hits == 1
    assert summary.hit_at_k == 0.5
    assert summary.mean_reciprocal_rank == 0.5
    assert summary.no_result_queries == 1
