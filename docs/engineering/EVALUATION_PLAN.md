# Evaluation Plan

Milestone 9 starts evaluation with deterministic local retrieval checks before adding LLMs,
embeddings, or vector search.

Implemented baseline:

- Dataset format: `evals/datasets/*.json`
- Sample smoke dataset: `evals/datasets/sample_retrieval_smoke.json`
- Sample source fixture: `evals/fixtures/sample_retrieval_source.txt`
- CLI: `python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_smoke.json`
- Metrics: `hit@k`, mean reciprocal rank, and no-result query count

Milestone 17 benchmark v1:

- Benchmark dataset: `evals/datasets/retrieval_benchmark_v1.json`
- Benchmark fixture: `evals/fixtures/retrieval_benchmark_v1_source.txt`
- Seed command: `python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset`
- Compare command: `python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes`
- Scope: natural-language questions over methods, results, table-like evidence, figure-caption-like evidence, limitations, and stable evidence definitions

Milestone 18 report generation:

- JSON report command: `python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json`
- Markdown report command: `python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-markdown`
- Combined report command: `python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown`
- Output directory: `evals/runs/`, ignored by Git
- Markdown sections: run metadata, metrics table, per-question result table, interpretation notes, and limitations

See `docs/engineering/EVALUATION.md` for the current runnable workflow.

Future evaluation work:

- Add curated scientific-paper question sets.
- Add evidence-type labels for text, table, figure, equation, caption, and layout evidence.
- Add semantic retrieval metrics after embeddings are introduced.
- Add answer faithfulness checks after LLM answer synthesis exists.
