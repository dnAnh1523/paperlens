from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.services.retrieval_service import (
    RetrievalBackendUnavailableError,
    RetrievalMode,
    get_retrieval_backend_status,
    search_chunks,
)

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
ALLOWED_EVIDENCE_TYPES = {
    "method",
    "result",
    "table",
    "figure_caption",
    "limitation",
    "definition",
}


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    question: str
    expected_terms: list[str]
    expected_answer_terms: list[str]
    expected_document_filename: str | None = None
    expected_chunk_text_contains: list[str] | None = None
    notes: str | None = None
    difficulty: str | None = None
    evidence_type: str | None = None

    @property
    def required_chunk_terms(self) -> list[str]:
        if self.expected_chunk_text_contains:
            return self.expected_chunk_text_contains
        if self.expected_terms:
            return self.expected_terms
        return self.expected_answer_terms


@dataclass(frozen=True)
class EvalDataset:
    name: str
    description: str | None
    default_k: int
    cases: list[EvalCase]


@dataclass(frozen=True)
class RetrievedEvidence:
    rank: int
    score: float
    backend: str
    document_id: str
    document_title: str
    document_filename: str
    chunk_id: str
    chunk_index: int
    chunk_text: str


@dataclass(frozen=True)
class CaseEvaluationResult:
    case_id: str
    question: str
    hit: bool
    hit_rank: int | None
    reciprocal_rank: float
    result_count: int
    no_results: bool
    matched_chunk_id: str | None
    matched_document_filename: str | None
    notes: str | None
    difficulty: str | None
    evidence_type: str | None
    retrieved: list[RetrievedEvidence]


@dataclass(frozen=True)
class EvaluationSummary:
    dataset_name: str
    total_cases: int
    k: int
    retrieval_mode: str
    retrieval_backend: str
    fts5_available: bool
    hits: int
    hit_at_k: float
    mean_reciprocal_rank: float
    no_result_queries: int


@dataclass(frozen=True)
class EvaluationReport:
    summary: EvaluationSummary
    results: list[CaseEvaluationResult]


@dataclass(frozen=True)
class ModeComparisonResult:
    mode: str
    available: bool
    backend: str | None
    report: EvaluationReport | None = None
    error: str | None = None


@dataclass(frozen=True)
class EvaluationComparisonReport:
    dataset_name: str
    k: int
    total_cases: int
    fts5_available: bool
    modes: list[ModeComparisonResult]


def _coerce_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError(f"{field_name} must be a string or list of strings.")


def _coerce_optional_choice(value: Any, field_name: str, allowed: set[str]) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {allowed_values}.")
    return normalized


def load_dataset(dataset_path: str | Path) -> EvalDataset:
    path = Path(dataset_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases_payload = payload.get("cases")
    if not isinstance(cases_payload, list) or not cases_payload:
        raise ValueError("Evaluation dataset must contain a non-empty 'cases' list.")

    cases: list[EvalCase] = []
    for index, raw_case in enumerate(cases_payload, start=1):
        if not isinstance(raw_case, dict):
            raise ValueError(f"Case {index} must be an object.")
        question = raw_case.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Case {index} must contain a non-empty question.")

        case_id = raw_case.get("id") or raw_case.get("case_id") or f"case-{index}"
        if not isinstance(case_id, str):
            raise ValueError(f"Case {index} id must be a string.")

        expected_document_filename = raw_case.get("expected_document_filename")
        if expected_document_filename is not None and not isinstance(expected_document_filename, str):
            raise ValueError(f"Case {index} expected_document_filename must be a string.")

        notes = raw_case.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise ValueError(f"Case {index} notes must be a string.")

        cases.append(
            EvalCase(
                case_id=case_id,
                question=question.strip(),
                expected_terms=_coerce_string_list(raw_case.get("expected_terms"), "expected_terms"),
                expected_answer_terms=_coerce_string_list(
                    raw_case.get("expected_answer_terms"),
                    "expected_answer_terms",
                ),
                expected_document_filename=expected_document_filename,
                expected_chunk_text_contains=_coerce_string_list(
                    raw_case.get("expected_chunk_text_contains"),
                    "expected_chunk_text_contains",
                ),
                notes=notes,
                difficulty=_coerce_optional_choice(
                    raw_case.get("difficulty"),
                    "difficulty",
                    ALLOWED_DIFFICULTIES,
                ),
                evidence_type=_coerce_optional_choice(
                    raw_case.get("evidence_type"),
                    "evidence_type",
                    ALLOWED_EVIDENCE_TYPES,
                ),
            )
        )

    name = payload.get("name") or path.stem
    if not isinstance(name, str):
        raise ValueError("Dataset name must be a string.")

    description = payload.get("description")
    if description is not None and not isinstance(description, str):
        raise ValueError("Dataset description must be a string.")

    default_k = payload.get("default_k", 5)
    if not isinstance(default_k, int) or default_k < 1:
        raise ValueError("default_k must be a positive integer.")

    return EvalDataset(name=name, description=description, default_k=default_k, cases=cases)


def evidence_matches_case(evidence: RetrievedEvidence, eval_case: EvalCase) -> bool:
    if eval_case.expected_document_filename:
        expected_filename = eval_case.expected_document_filename.casefold()
        if evidence.document_filename.casefold() != expected_filename:
            return False

    required_terms = eval_case.required_chunk_terms
    if required_terms:
        chunk_text = evidence.chunk_text.casefold()
        return all(term.casefold() in chunk_text for term in required_terms)

    return eval_case.expected_document_filename is not None


def evaluate_case(eval_case: EvalCase, retrieved: list[RetrievedEvidence]) -> CaseEvaluationResult:
    hit_rank: int | None = None
    matched: RetrievedEvidence | None = None
    for evidence in retrieved:
        if evidence_matches_case(evidence, eval_case):
            hit_rank = evidence.rank
            matched = evidence
            break

    reciprocal_rank = 1 / hit_rank if hit_rank is not None else 0.0
    return CaseEvaluationResult(
        case_id=eval_case.case_id,
        question=eval_case.question,
        hit=hit_rank is not None,
        hit_rank=hit_rank,
        reciprocal_rank=reciprocal_rank,
        result_count=len(retrieved),
        no_results=len(retrieved) == 0,
        matched_chunk_id=matched.chunk_id if matched else None,
        matched_document_filename=matched.document_filename if matched else None,
        notes=eval_case.notes,
        difficulty=eval_case.difficulty,
        evidence_type=eval_case.evidence_type,
        retrieved=retrieved,
    )


def compute_summary(
    dataset_name: str,
    results: list[CaseEvaluationResult],
    k: int,
    retrieval_mode: str = "auto",
    retrieval_backend: str = "like",
    fts5_available: bool = False,
) -> EvaluationSummary:
    total_cases = len(results)
    hits = sum(1 for result in results if result.hit)
    reciprocal_rank_sum = sum(result.reciprocal_rank for result in results)
    return EvaluationSummary(
        dataset_name=dataset_name,
        total_cases=total_cases,
        k=k,
        retrieval_mode=retrieval_mode,
        retrieval_backend=retrieval_backend,
        fts5_available=fts5_available,
        hits=hits,
        hit_at_k=hits / total_cases if total_cases else 0.0,
        mean_reciprocal_rank=reciprocal_rank_sum / total_cases if total_cases else 0.0,
        no_result_queries=sum(1 for result in results if result.no_results),
    )


def run_retrieval_eval(
    db: Session,
    dataset: EvalDataset,
    limit: int | None = None,
    mode: str = "auto",
) -> EvaluationReport:
    k = limit or dataset.default_k
    backend_status = get_retrieval_backend_status(db, mode=mode)
    if mode == "fts5" and not backend_status.fts5_available:
        raise RetrievalBackendUnavailableError("SQLite FTS5 is not available in this environment.")

    results: list[CaseEvaluationResult] = []
    active_backend = backend_status.active_mode

    for eval_case in dataset.cases:
        search_results = search_chunks(db, query=eval_case.question, limit=k, mode=mode)
        if search_results:
            active_backend = search_results[0].backend
        retrieved = [
            RetrievedEvidence(
                rank=result.rank,
                score=result.score,
                backend=result.backend,
                document_id=result.document.id,
                document_title=result.document.title,
                document_filename=result.document.original_filename,
                chunk_id=result.chunk.chunk_id,
                chunk_index=result.chunk.chunk_index,
                chunk_text=result.chunk.text,
            )
            for result in search_results
        ]
        results.append(evaluate_case(eval_case, retrieved))

    return EvaluationReport(
        summary=compute_summary(
            dataset.name,
            results,
            k,
            retrieval_mode=mode,
            retrieval_backend=active_backend,
            fts5_available=backend_status.fts5_available,
        ),
        results=results,
    )


def run_retrieval_eval_comparison(
    db: Session,
    dataset: EvalDataset,
    limit: int | None = None,
) -> EvaluationComparisonReport:
    k = limit or dataset.default_k
    backend_status = get_retrieval_backend_status(db, mode=RetrievalMode.AUTO)
    mode_results: list[ModeComparisonResult] = []

    for mode in (RetrievalMode.LIKE, RetrievalMode.FTS5, RetrievalMode.AUTO):
        if mode == RetrievalMode.FTS5 and not backend_status.fts5_available:
            mode_results.append(
                ModeComparisonResult(
                    mode=mode.value,
                    available=False,
                    backend=None,
                    report=None,
                    error="SQLite FTS5 is not available in this environment.",
                )
            )
            continue

        try:
            report = run_retrieval_eval(db, dataset, limit=limit, mode=mode.value)
        except RetrievalBackendUnavailableError as exc:
            mode_results.append(
                ModeComparisonResult(
                    mode=mode.value,
                    available=False,
                    backend=None,
                    report=None,
                    error=str(exc),
                )
            )
            continue

        mode_results.append(
            ModeComparisonResult(
                mode=mode.value,
                available=True,
                backend=report.summary.retrieval_backend,
                report=report,
                error=None,
            )
        )

    return EvaluationComparisonReport(
        dataset_name=dataset.name,
        k=k,
        total_cases=len(dataset.cases),
        fts5_available=backend_status.fts5_available,
        modes=mode_results,
    )


def report_to_dict(report: EvaluationReport | EvaluationComparisonReport) -> dict[str, Any]:
    return asdict(report)


def format_report(report: EvaluationReport) -> str:
    summary = report.summary
    lines = [
        f"Retrieval evaluation: {summary.dataset_name}",
        f"Mode: {summary.retrieval_mode}",
        f"Backend: {summary.retrieval_backend}",
        f"SQLite FTS5 available: {summary.fts5_available}",
        f"Cases: {summary.total_cases}",
        f"hit@{summary.k}: {summary.hit_at_k:.3f} ({summary.hits}/{summary.total_cases})",
        f"MRR: {summary.mean_reciprocal_rank:.3f}",
        f"No-result queries: {summary.no_result_queries}",
        "",
        "Case results:",
    ]
    for result in report.results:
        status = "HIT" if result.hit else "MISS"
        rank = f"rank {result.hit_rank}" if result.hit_rank is not None else "no match"
        metadata = ", ".join(
            value
            for value in (result.difficulty, result.evidence_type)
            if value is not None
        )
        metadata_suffix = f" ({metadata})" if metadata else ""
        lines.append(
            f"- [{status}] {result.case_id}{metadata_suffix}: "
            f"{rank}, {result.result_count} result(s)"
        )
        if result.matched_document_filename and result.matched_chunk_id:
            lines.append(
                f"  matched {result.matched_document_filename} chunk {result.matched_chunk_id[:8]}"
            )
        if result.no_results:
            lines.append("  retrieval returned no chunks")
        if result.notes:
            lines.append(f"  notes: {result.notes}")
    return "\n".join(lines)


def _case_status(result: CaseEvaluationResult) -> str:
    if result.hit_rank is not None:
        return f"HIT rank {result.hit_rank}"
    if result.no_results:
        return "MISS no results"
    return "MISS no match"


def format_comparison_report(report: EvaluationComparisonReport) -> str:
    lines = [
        f"Retrieval comparison: {report.dataset_name}",
        f"Cases: {report.total_cases}",
        f"k: {report.k}",
        f"SQLite FTS5 available: {report.fts5_available}",
        "",
        "Mode summary:",
    ]

    for mode_result in report.modes:
        if not mode_result.available or mode_result.report is None:
            lines.append(
                f"- {mode_result.mode}: unavailable"
                f" ({mode_result.error or 'backend unavailable'})"
            )
            continue

        summary = mode_result.report.summary
        lines.append(
            f"- {mode_result.mode}: backend={summary.retrieval_backend}, "
            f"hit@{summary.k}={summary.hit_at_k:.3f} "
            f"({summary.hits}/{summary.total_cases}), "
            f"MRR={summary.mean_reciprocal_rank:.3f}, "
            f"no-results={summary.no_result_queries}"
        )

    case_ids: list[str] = []
    for mode_result in report.modes:
        if mode_result.report is None:
            continue
        for result in mode_result.report.results:
            if result.case_id not in case_ids:
                case_ids.append(result.case_id)

    if case_ids:
        lines.extend(["", "Per-question summary:"])

    for case_id in case_ids:
        lines.append(f"- {case_id}")
        for mode_result in report.modes:
            if not mode_result.available or mode_result.report is None:
                lines.append(f"  {mode_result.mode}: unavailable")
                continue

            result_by_case = {
                result.case_id: result for result in mode_result.report.results
            }
            case_result = result_by_case.get(case_id)
            if case_result is None:
                lines.append(f"  {mode_result.mode}: not evaluated")
                continue
            lines.append(f"  {mode_result.mode}: {_case_status(case_result)}")

    return "\n".join(lines)


class EvalRunner:
    """Runs local deterministic retrieval evaluations."""

    def run(
        self,
        eval_set_path: str,
        db: Session,
        limit: int | None = None,
        mode: str = "auto",
        compare_modes: bool = False,
    ) -> dict[str, Any]:
        dataset = load_dataset(eval_set_path)
        if compare_modes:
            comparison_report = run_retrieval_eval_comparison(db, dataset, limit=limit)
            return report_to_dict(comparison_report)
        report = run_retrieval_eval(db, dataset, limit=limit, mode=mode)
        return report_to_dict(report)
