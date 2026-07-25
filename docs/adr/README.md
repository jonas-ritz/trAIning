# Architecture Decision Records

Each ADR captures one decision: the context, the options considered, what was chosen, and what
follows from it. They are immutable — a decision that turns out wrong is not edited, it is
superseded by a new ADR that says so.

Write an ADR whenever a future reader (including future me) would otherwise have to
reverse-engineer *why* something is the way it is.

| # | Decision | Status |
|---|---|---|
| [0001](0001-garmindb-as-primary-source.md) | GarminDB as the primary data source, Strava as fallback | Accepted |
| [0002](0002-llm-interprets-code-measures.md) | The LLM interprets and builds; deterministic code measures | Accepted |
| [0003](0003-no-acwr-or-monotony.md) | No ACWR or Foster monotony for heterogeneous training | Accepted |
| [0004](0004-claude-via-foundry.md) | Claude via Microsoft Foundry, not the Anthropic API | Accepted |
| [0005](0005-table-per-type-activities.md) | Table-per-type for activity detail | Accepted |
| [0006](0006-google-calendar-one-way.md) | Google Calendar as a one-way sink | Accepted |
| [0007](0007-rolling-window-stateless-collector.md) | Rolling window instead of a persisted collector state | Accepted |
| [0008](0008-athlete-data-split-by-owner.md) | Athlete data split by owner, not by topic | Accepted |
| [0009](0009-plan-first-chat-optional.md) | Plan-first, chat optional | Accepted |
| [0010](0010-pwa-not-native.md) | PWA instead of a native iOS app | Accepted |
| [0011](0011-manual-weight-entry.md) | Strength weight entered by the user, not read from the device | Accepted |

Template: [template.md](template.md)
