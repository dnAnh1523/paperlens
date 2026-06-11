# Evaluation

Milestone 9 adds a local retrieval evaluation harness. It is deterministic and does not call an LLM,
embedding model, vector database, cloud service, Docker service, or paid API.

## Dataset format

Retrieval datasets are JSON files with a top-level `cases` list:

```json
{
  "name": "sample_retrieval_eval",
  "description": "Optional description",
  "default_k": 5,
  "cases": [
    {
      "id": "local-stack",
      "question": "What local stack does PaperLens use?",
      "expected_terms": ["SQLite", "local folders"],
      "expected_answer_terms": ["metadata"],
      "expected_document_filename": "sample_retrieval_source.txt",
      "expected_chunk_text_contains": ["SQLite for metadata"],
      "notes": "Optional notes"
    }
  ]
}
```

Supported case fields:

- `question`: required search query.
- `expected_terms`: optional string or list of strings expected in a retrieved evidence chunk.
- `expected_answer_terms`: optional string or list of strings, used when `expected_terms` is absent.
- `expected_document_filename`: optional exact source filename match.
- `expected_chunk_text_contains`: optional string or list of strings that overrides term matching for the chunk text.
- `notes`: optional evaluator notes.

A case is a hit when a retrieved chunk matches the expected filename, if provided, and contains all
required expected chunk terms.

## Sample dataset

Committed sample files:

```text
evals/fixtures/sample_retrieval_source.txt
evals/datasets/sample_retrieval_eval.json
```

To run the sample as a hit-producing eval, first upload `evals/fixtures/sample_retrieval_source.txt`
through the web UI and click `Prepare document`. Then run from the repository root:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_eval.json
```

The script defaults to the same local app state used by the backend development setup:

```text
apps/api/data/sqlite/paperlens.db
apps/api/data/storage
```

Environment variables `DATABASE_URL` and `LOCAL_STORAGE_ROOT` can override those paths.

## Metrics

The report prints:

- `hit@k`: fraction of cases where a matching chunk appears in the top `k` results.
- `MRR`: mean reciprocal rank of the first matching chunk.
- `No-result queries`: number of cases where retrieval returned no chunks.

Override `k` with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_eval.json --limit 10
```

## JSON reports

Write a local JSON report with:

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_eval.json --write-json
```

Generated reports are written under `evals/runs/`, which is gitignored.

## Limitations

- Metrics only check lexical retrieval against expected filenames and chunk text terms.
- There is no LLM judge, answer faithfulness score, semantic similarity, reranking, or embedding recall yet.
- The harness evaluates current local SQLite state, so documents must be uploaded, ingested, and chunked first.

## PDF notes

PDF eval cases should use text-layer PDFs for now. Milestone 10 preserves page markers in
`extracted_text.txt` and writes page-level text artifacts, so retrieval cases can target terms that
appear on specific pages. Scanned PDFs without a text layer are expected to fail ingestion until OCR is
implemented.
