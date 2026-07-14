# ADR-0003: No ACWR or Foster monotony for heterogeneous training

**Status:** Accepted
**Date:** 2026-07

## Context

The obvious load-management metrics from the sports-science literature are the Acute:Chronic
Workload Ratio (7-day vs 28-day load) and Foster's monotony/strain. They are well known, easy to
implement, and would look impressive in a dashboard.

## Options considered

- **Implement them anyway.** Familiar, cheap, superficially credible.
- **Leave them out and build load metrics from the interpretation fields instead.**

## Decision

Do not implement ACWR or Foster monotony.

Both come from elite single-sport settings with homogeneous, comparable load. They assume that
"load" is one currency. Squeezing a padel evening with friends, a hypertrophy session, and a long
run into one number and then taking a ratio of it produces a figure that looks precise and means
very little.

Instead, load is tracked per system and per muscle group, weighted by the LLM-assigned
`fatigue_score` from the interpretation layer, over rolling windows.

## Consequences

- No pseudo-precision in the dashboard. Fewer impressive-looking numbers, more defensible ones.
- Load management reasoning is grounded in fields that were assigned *with knowledge of what the
  session actually was*, rather than in a formula that never saw the sport type.
- If a genuinely validated multi-sport load model appears later, this ADR gets superseded.
- Being able to explain *why these metrics were rejected* is worth more in an interview than
  having implemented them.
