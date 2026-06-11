# Evaluation Plan

Milestone 9 starts evaluation with deterministic local retrieval checks before adding LLMs,
embeddings, or vector search.

Implemented baseline:

- Dataset format: `evals/datasets/*.json`
- Sample dataset: `evals/datasets/sample_retrieval_eval.json`
- Sample source fixture: `evals/fixtures/sample_retrieval_source.txt`
- CLI: `python scripts/run_retrieval_eval.py --dataset evals/datasets/sample_retrieval_eval.json`
- Metrics: `hit@k`, mean reciprocal rank, and no-result query count

See `docs/engineering/EVALUATION.md` for the current runnable workflow.

Future evaluation work:

- Add curated scientific-paper question sets.
- Add evidence-type labels for text, table, figure, equation, caption, and layout evidence.
- Add semantic retrieval metrics after embeddings are introduced.
- Add answer faithfulness checks after LLM answer synthesis exists.
