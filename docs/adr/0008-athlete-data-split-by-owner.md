# ADR-0008: Athlete data split by owner, not by topic

**Status:** Accepted
**Date:** 2026-07

## Context

The system needs to hold: personal facts (age, height, HRmax), body composition (weight, body fat),
injury history, goals, and whatever the agent gradually learns about the athlete.

The tempting design is one `Profile` table holding all of it. That design is quietly wrong in two
different ways.

## Decision

Split by **owner**, not by topic. Four kinds of truth, four homes.

| Table | Owner | Rule |
|---|---|---|
| `AthleteProfile` | user only | Birth date (not age — ages go stale), height, HRmax + `HrMaxSource`, preferences, equipment, time budget. **The agent may not write here.** |
| `BodyMeasurement` | time series | Weight, body fat, muscle mass, with a date. |
| `Goal`, `Injury` | user or agent | Agent may create them; always tagged with `Source`. |
| `AgentMemory` | agent only | Rolling machine-written summary. |

## Consequences

- **Weight and body fat are never profile fields.** Storing them there means overwriting your own
  history on every update — and the history is exactly what the coach needs ("weight flat for eight
  weeks, but the goal is mass"). A state is not a trajectory. This is the same mistake class as
  storing only average heart rate (ADR-0005).
- **`HrMaxSource` (`measured` | `estimated`) is not cosmetic.** It tells the metrics engine how much
  to trust the zone boundaries. An estimated HRmax makes time-in-zone a rough signal; a measured one
  makes it a real one.
- **Injuries carry structured `Constraints`** ("no deep knee flexion under load"), not prose. Free
  text is something the agent can only *hope* to honour; a structured constraint is something it can
  be held to — and something the eval harness can assert on.
- The user can always see what the system *believes* about them (`AgentMemory`), separately from what
  they *told* it (`AthleteProfile`). The agent can never silently rewrite the latter.
