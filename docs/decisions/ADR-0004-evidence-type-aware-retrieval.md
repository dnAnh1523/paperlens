# ADR-0004: Evidence-Type-Aware Retrieval

## Status

Proposed

M1-M18 implement the local text/page-aware retrieval foundation only. Full evidence-type-aware
retrieval for tables, figures, charts, equations, captions, and page images remains future work.

## Context

Scientific papers contain heterogeneous evidence. Text-only chunks are insufficient for many questions.

## Decision

Represent and retrieve evidence by type: text, table, figure, chart, equation, caption, and page image.

## Consequences

- The retrieval pipeline is more complex.
- Evaluation can measure which evidence types improve performance.
- Citations can point to precise page/assets rather than only text chunks.
