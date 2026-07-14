# ADR-0002: The LLM interprets and builds; deterministic code measures

**Status:** Accepted
**Date:** 2026-07

## Context

The training data is heterogeneous — gym sessions, runs, rides, padel, five-a-side, circuits. An
obvious temptation is to hand everything to the LLM and let it work out what happened, since a
rigid formula struggles to compare a squat session with an interval run.

## Options considered

- **LLM does everything.** Dump raw history into context, let it reason. Attractive because it
  handles heterogeneity naturally. But: expensive (months of samples per call), slow, and
  unreliable — models do not sum 200 rows correctly. Worse, it is *not reproducible*: the same
  question twice yields two different volume figures, and you can never test whether the agent
  improved.
- **Formulas do everything.** Reproducible, but no formula meaningfully compares padel to a
  tempo run.
- **Split by what each is actually good at.**

## Decision

Three layers:

1. **Metrics Engine (C#, deterministic).** Measures. Time in HR zones, interval structure, HRR,
   aerobic decoupling, tonnage, hard sets per muscle group, e1RM, RHR baseline deviation. Every
   formula documented with a literature citation. 100 % test coverage.
2. **Interpretation (LLM, per session).** Translates measurements into *meaning*: what kind of
   session this was, what stimulus it delivered, how well it was executed, how it relates to goals.
   This is the layer that absorbs heterogeneity.
3. **Agent (LLM).** Receives metrics and interpretations as tool results. Decides, explains, plans.

The LLM never computes a number it could be handed instead.

## Consequences

- Interpretation runs once per activity and is persisted, never recomputed.
- The metrics engine is the only code that does arithmetic. It is therefore the only code that
  needs exhaustive testing.
- Agent behaviour becomes evaluable: given the same DB snapshot, the inputs are identical, so
  the eval harness measures the agent, not noise in the arithmetic.
- Cost drops sharply: the agent reasons over a page of metrics, not a year of samples.
- **This is the project's strongest architectural argument.** It is the difference between a demo
  and a system somebody would trust.
