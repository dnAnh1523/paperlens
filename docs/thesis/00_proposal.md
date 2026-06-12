# PaperLens Thesis Proposal

## Working title

PaperLens: Evidence-Type-Aware Multimodal Retrieval-Augmented Generation for Scientific Paper Understanding

## Motivation

Scientific papers contain important information in text, figures, tables, equations, captions, and page layout. Text-only retrieval-augmented generation can fail when the answer depends on visual, tabular, mathematical, or layout-dependent evidence.

## Problem statement

This project studies and implements the foundations for an evidence-type-aware multimodal RAG system
that can eventually retrieve and reason over heterogeneous evidence in scientific and technical papers.
The current M1-M18 implementation is a local evidence-grounded retrieval and evidence-preview system,
not a completed multimodal RAG system.

## Research questions

1. Does evidence-type-aware retrieval improve answer accuracy over text-only retrieval?
2. Does using visual page/figure/table evidence improve answer faithfulness?
3. Which evidence types are most responsible for failures in text-only RAG?
4. How should structured tables be combined with multimodal model reasoning?

## Expected contribution

- A working local-native foundation for scientific document ingestion, chunking, retrieval, source
  inspection, and deterministic evidence-preview chat.
- A modular retrieval pipeline that can later support evidence-type-aware and multimodal variants.
- An evaluation framework comparing local lexical retrieval modes before adding embeddings, OCR,
  table/figure extraction, or LLM answer synthesis.
- A documented engineering artifact suitable for reproducible applied CS work.

## Current scope boundary

M1-M18 do not include OCR, table extraction, figure extraction, equation parsing, real embeddings,
vector retrieval, multimodal vision, or LLM answer synthesis. Those capabilities are future work.
