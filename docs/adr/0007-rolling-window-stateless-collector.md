# ADR-0007: Rolling window instead of a persisted collector state

**Status:** Accepted
**Date:** 2026-07

## Context

GarminDB's `--latest` flag only knows what is new because it can see the files it previously
downloaded on local disk. An Azure Container Apps Job is ephemeral: the filesystem is discarded
after every run. On the next night, GarminDB would have no memory and would re-download everything
from the configured start date.

## Options considered

- **Persistent volume.** Mount Azure Files at `~/HealthData` so GarminDB keeps its state and
  `--latest` behaves as designed. Correct, but it adds a stateful component, a mount, and a failure
  mode to an otherwise disposable job — and it does not self-heal after an outage; it simply falls
  behind.
- **Rolling window.** On every run, set the start dates to "today minus N days" and re-fetch that
  window unconditionally. Stateless. Costs redundant downloads.

## Decision

Rolling window, N = 7 days. The collector stays completely stateless and disposable.

The self-healing property decided it: if the job fails for three nights, the fourth run silently
backfills the gap. A persisted volume would just be three nights behind.

## Consequences

These are **requirements on other code**, not side notes:

- **Blob names must be deterministic**, derived from the Garmin activity ID:
  `raw/activities/{activityId}.fit`, `raw/wellness/{date}.json`. Re-uploading the same activity
  overwrites the same blob instead of creating seven copies.
- **Ingest must be idempotent.** The same blob is re-uploaded (and re-triggers the function) up to
  seven times, and Azure blob triggers can double-deliver regardless. Deduplication via `DedupKey`
  must make reprocessing a no-op. There is an explicit test for this: ingest the same file twice,
  assert one row.
- **Interpretation must not re-run** on an activity that already has a `SessionInterpretation`.
  Otherwise the rolling window turns 1 LLM call per session into 7. This is the cheapest mistake
  to make and the most expensive to leave in.
- *Optional later:* check blob existence before uploading and skip unchanged files. Saves triggers.
  Not required for correctness — the idempotency above already guarantees that.
- Widening the backfill window after a long outage is a config change, not a code change.
