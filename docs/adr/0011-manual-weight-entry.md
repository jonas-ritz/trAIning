# ADR-0011: Strength weight is entered by the user, not read from the device

**Status:** Accepted
**Date:** 2026-07

## Context

A Phase 0 inspection of real FIT files from the FR255 settled what the watch does and does not
record for strength training. The findings:

- **Reps: recorded.** The watch counts repetitions per set reliably.
- **Set structure: recorded.** Active sets and rest periods, with durations and timestamps.
- **Heart rate: recorded**, per-second, even in the gym (~1584 records in a 50-minute session).
- **Exercise type: recorded, but encoded.** A FIT enum tuple, e.g. `category=(65534, 7, 0)`, where
  65534 is Garmin's "unknown / custom" marker. Not human-readable as-is.
- **Weight: only present when the athlete entered it.** And it arrives in three distinct states:
  - `None` — nothing was entered
  - `0.0` — deliberately zero (bodyweight movement, or "0" typed in)
  - a real value, e.g. `52.0`

The watch cannot measure external load. It only has weight if the athlete typed it — on the watch
or in Garmin Connect.

This matters because the weight-dependent half of the metrics engine (tonnage, e1RM, PR detection,
stagnation) is exactly the half a hypertrophy goal depends on. Without weight, the coach cannot
tell you your squat has stalled.

## Options considered

- **Live logging in the gym.** Enter weight set-by-set on the phone during training. Interrupts the
  session; the original plan, and a poor one.
- **Post-session completion.** The session arrives from the watch with its skeleton already built —
  exercises detected, sets and reps counted, rests measured. The athlete fills in only the missing
  weights (and corrects mis-detected exercises) afterwards, in ~30 seconds.
- **Give up on weight-based metrics.** Unacceptable — it guts the strength side of the coach.

## Decision

Post-session completion. The watch provides the skeleton; the user provides the load.

`weight=0.0` and `weight=None` are treated as **different states**, not merged. Conflating them
corrupts tonnage.

## Consequences

- **`StrengthSet` gains provenance fields:**
  - `WeightKg` is **nullable**. Null = not entered; the metrics engine must skip it, not treat it as zero.
  - `IsBodyweight` (bool) distinguishes a deliberate zero from a missing value.
  - `WeightSource` (`device` | `user` | `estimated`) — parallel to `HrMaxSource` (ADR-0008). Tells the
    metrics engine how far to trust the number.
  - `RepsSource` and `ExerciseSource` (`device` | `user`) — reps come from the watch, exercise may be
    device-detected or user-corrected. `WasDetected` from the earlier draft is subsumed by these.
- **The metrics engine is honest about gaps.** A weight-dependent metric returns "unavailable" for a
  session with unentered weights, rather than a wrong number. This is stated in the metric's contract
  and tested.
- **Gym-set completion moves from Phase 6 to Phase 3.** Without weights the metrics engine is half-blind,
  so completion cannot be a late add-on. It ships with the ingest/metrics work.
- **The PWA needs a per-session completion view:** the skeleton pre-filled from the watch, weight and
  optional RPE as the only required inputs, exercise name editable. This is the primary manual-entry
  surface — and the reason the app earns its place alongside the watch.
- Exercise decoding (the FIT enum tuple → a readable name) is required for this view to be usable.
  Tracked separately (see the exercise-map work); this ADR depends on it but does not solve it.