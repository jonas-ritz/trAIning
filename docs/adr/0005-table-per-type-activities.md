# ADR-0005: Table-per-type for activity detail

**Status:** Accepted
**Date:** 2026-07

## Context

A 5×5 squat session and a 6×800 m interval run share almost nothing except a start time and a
duration. A single wide `Activity` table would be mostly nulls, and would quietly lose the detail
that makes coaching possible.

A specific failure mode to avoid: storing only *average* heart rate. An average tells you nothing
about an interval session. The information lives in the trace.

## Options considered

- **One wide table.** Simple, and wrong. Sport-specific columns proliferate; most rows are null;
  time-series data has nowhere to go.
- **JSON blob per activity.** Flexible, unqueryable, untestable.
- **Common core + typed detail tables.**

## Decision

A deliberately thin `Activity` core (time, duration, sport type, summary values, pointers to which
detail exists), plus:

- `ActivitySample` — per-second records: HR, speed, cadence, power, altitude. This is what makes
  time-in-zone, interval detection and aerobic decoupling possible at all.
- `ActivityLap` — work/rest structure. This is where 6×800 m stops being "a 10 km run".
- `StrengthSet` — exercise, set index, reps, weight, rest. Structurally unlike anything in a run,
  so it gets its own table.
- `DailyWellness` — sleep, RHR, stress, HRV, weight.

## Consequences

- ~3600 sample rows per hour of training; roughly 1M rows/year at current volume. Trivial for Azure
  SQL's 32 GB free tier.
- **Sample retention is deliberately unsolved.** If it ever hurts, samples move to Blob (Parquet)
  and only derived metrics stay in SQL. Not a problem yet, so not solved yet.
- `HasSamples` / `HasSets` / `HasLaps` flags on the core tell consumers which detail exists without
  a join.
- The metrics engine can be honest: it computes what the data supports, and nothing more.
