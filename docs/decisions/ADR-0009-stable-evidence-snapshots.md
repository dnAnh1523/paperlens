# ADR-0009: Preserve Stable Evidence Snapshots for Chat History

## Status

Accepted

## Context

PaperLens chat responses are deterministic evidence previews grounded in retrieved chunks. Users can
inspect source context behind evidence cards. However, chunks can be regenerated when a document is
re-ingested or re-chunked, and old chunk IDs may disappear.

If historical assistant messages only referenced live chunk IDs, old evidence cards could become
uninspectable after re-chunking.

## Decision

PaperLens will store answer-time evidence snapshots with assistant messages:

- excerpt snapshot
- full chunk text snapshot
- document title and filename snapshot
- chunk index snapshot
- character offsets
- page metadata when available
- estimated token count

Source preview should prefer live chunk context when available and fall back to the stored snapshot
when the live chunk is gone. The UI should mark snapshot fallback as stale rather than failing the
whole evidence preview.

## Consequences

Positive:

- Historical chat evidence remains inspectable after re-chunking or deletion.
- Reports and demos can explain exactly what evidence was shown at answer time.
- The behavior supports reproducible debugging without requiring immutable chunk IDs.

Negative:

- Snapshot text can become stale relative to the current document state.
- Snapshot fallback cannot reconstruct neighboring live chunks after deletion.
- The feature preserves extracted text context only; it does not render original PDF pages or page
  images.
