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

---

## Correction (2026-07, after Phase 0)

The decision above stands unchanged — stateless, rolling, self-healing. Only the *implementation*
turned out to be split, which the original text obscured by calling it simply a "7-day window".

GarminDB does not steer all data types the same way:

- **Wellness** (sleep, resting HR, stress, monitoring) is date-driven. The config takes real start
  dates, so "today minus 7 days" is literal:
  ```json
  "sleep_start_date": "...", "rhr_start_date": "...", "monitoring_start_date": "..."
  ```
- **Activities** are *count*-driven, not date-driven. There is no activity start-date field. The
  config takes a number:
  ```json
  "download_latest_activities": 25
  ```
  `--latest` for activities means "the last N", not "since date X".

**Implementation of the rolling window is therefore two-part:** set the wellness start dates to
today minus 7 days, and set `download_latest_activities` to a count that comfortably exceeds 7 days
of training. At the current training frequency, 20–25 is safe. A fixed generous count is preferred
over dynamically computing one — that would be over-engineering for a single user.

The self-healing property is preserved on both sides: a wider date range and a larger count both
just re-fetch more, and dedup absorbs the overlap.