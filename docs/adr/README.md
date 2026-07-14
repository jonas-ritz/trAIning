# Architecture Decision Records

Each ADR captures a decision, the options that were rejected, and why. They are **immutable**:
a decision that turns out wrong gets superseded by a new ADR, not edited in place. See
[`template.md`](template.md) for the format.

| ADR | Decision |
|---|---|
| [0001](0001-garmindb-as-primary-source.md) | GarminDB as the primary data source, Strava as fallback |
| [0002](0002-llm-interprets-code-measures.md) | The LLM interprets and builds; deterministic code measures |
| [0003](0003-no-acwr-or-monotony.md) | No ACWR or Foster monotony for heterogeneous training |
| [0004](0004-claude-via-foundry.md) | Claude via Microsoft Foundry, not the Anthropic API |
| [0005](0005-table-per-type-activities.md) | Table-per-type for activity detail |
| [0006](0006-google-calendar-one-way.md) | Google Calendar as a one-way sink |
| [0007](0007-rolling-window-stateless-collector.md) | Rolling window instead of a persisted collector state |
| [0008](0008-athlete-data-split-by-owner.md) | Athlete data split by owner, not by topic |
| [0009](0009-plan-first-chat-optional.md) | Plan-first, chat optional |
| [0010](0010-pwa-not-native.md) | PWA instead of a native iOS app |
