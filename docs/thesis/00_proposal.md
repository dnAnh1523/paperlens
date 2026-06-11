# PaperLens Thesis Proposal

## Working title

PaperLens: Evidence-Type-Aware Multimodal Retrieval-Augmented Generation for Scientific Paper Understanding

## Motivation

Scientific papers contain important information in text, figures, tables, equations, captions, and page layout. Text-only retrieval-augmented generation can fail when the answer depends on visual, tabular, mathematical, or layout-dependent evidence.

## Problem statement

This project studies and implements an evidence-type-aware multimodal RAG system that can retrieve and reason over heterogeneous evidence in scientific and technical papers.

## Research questions

1. Does evidence-type-aware retrieval improve answer accuracy over text-only retrieval?
2. Does using visual page/figure/table evidence improve answer faithfulness?
3. Which evidence types are most responsible for failures in text-only RAG?
4. How should structured tables be combined with multimodal model reasoning?

## Expected contribution

- A working end-to-end system for multimodal paper QA.
- A modular evidence-type-aware retrieval pipeline.
- An evaluation framework comparing text-only and multimodal variants.
- A documented engineering artifact suitable for reproducible applied CS work.
