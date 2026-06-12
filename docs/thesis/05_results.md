# Results

Current retrieval results are generated locally and should be read from Markdown/JSON reports under
`evals/runs/` after running the benchmark report command.

Reproduce the current benchmark report:

```powershell
python scripts/seed_eval_fixture.py --fixture evals/fixtures/retrieval_benchmark_v1_source.txt --reset
```

```powershell
python scripts/run_retrieval_eval.py --dataset evals/datasets/retrieval_benchmark_v1.json --compare-modes --write-json --write-markdown
```

Interpretation rules:

- Smoke test results confirm pipeline plumbing only.
- Benchmark v1 results are local, synthetic, and lexical.
- FTS5 results are evidence for this local fixture and SQLite build, not universal proof.
- No current result measures answer synthesis, multimodal reasoning, OCR, table extraction, figure
  extraction, equation extraction, semantic retrieval, or LLM faithfulness.
