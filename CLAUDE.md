# Training Coach

A personal training coach that plans on its own and listens when you have something to say.
Ingests everything recorded by a Garmin watch, measures what actually happened, and lets an AI
agent plan training from history, goals, optional conversation, and optional nutrition notes.
It works with zero user input; chat is an optional steering layer. It explains its reasoning,
replans when you push back, and writes sessions into Google Calendar.

Delivered as a PWA — a web app that installs to the iOS home screen, supports push
notifications, and works offline in the gym. One Blazor codebase, no App Store.

**Full spec: @docs/spec.md** — always check there before making architecture decisions.

## Stack

- .NET 10 (LTS), C# throughout — except one isolated Python container
- Blazor Web App as a PWA (iOS-installable, offline gym logging, web push)
- ASP.NET Core Web API
- EF Core → Azure SQL (free tier)
- Azure Container Apps, Container Apps Jobs, Functions, Blob Storage, Key Vault
- Claude via Microsoft Foundry (Entra auth, no API keys)
- Google Calendar API for scheduling (OAuth, dedicated training calendar, one-way sync)
- Bicep for IaC, GitHub Actions for CI/CD

## Core principles (non-negotiable)

**1. The LLM interprets and builds. Deterministic code measures.**
The metrics engine measures — from raw device data, with documented, tested, reproducible
formulas. The LLM interprets those measurements and builds plans from them. It NEVER computes
a number it could be handed instead. If you're tempted to let the LLM sum something: don't.

**2. Data sources are replaceable and isolated.**
The Garmin collector is an unofficial, fragile Python fetcher. It runs in its own container,
delivers only raw files to Blob Storage, and knows nothing about the domain model. Its SQLite
schema is NOT used — parsing happens in C# with the FIT SDK. All ingest goes through
`IActivitySource` so Strava can be swapped in later without touching the domain.

**3. The agent is autonomous by default, steerable on demand.**
It plans a week every Sunday from data alone — no conversation required. Chat is an optional
control surface: when the user says something, the plan adapts. The primary UI surface is the
plan, not the chat. The agent nudges after 5 days of silence, asks when it genuinely needs
input, and is otherwise quiet. Plans are superseded, never silently overwritten.

## Data ownership (easy to get wrong)

Athlete data is split by who owns it. Never collapse these into one profile table:
- `AthleteProfile` — user-configured, stable (birth date, height, HRmax + source, preferences).
  **The agent may NOT write here.**
- `BodyMeasurement` — a time series (weight, body fat). Never a profile field: overwriting it
  destroys the history the coach needs.
- `Injury` and `Goal` — structured, agent may create them, always marked with `Source`.
  Injuries carry machine-readable `Constraints`, not free text.
- `AgentMemory` — machine-written rolling summary, kept separate from human-authored config.

## Design

- **SOLID throughout.** Dependency Inversion at the ingest boundary; Single Responsibility in
  the metrics engine (one calculator per metric family, not a god class).
- **Abstract where a second implementation is known or the boundary is external.**
  `IActivitySource` is justified (Strava is planned). `IRepository<T>` over EF Core is not.
  No speculative abstraction — the second occurrence earns the interface, not the first.
- **Patterns where they carry weight:** Strategy for metric calculators, Adapter at the source
  boundary, Chain of Responsibility for the ingest pipeline, Command for agent tool calls.
  Use them when they name something real; don't decorate.

## Documentation (explicitly required, not an afterthought)

- **README.md** kept current: what it is, how to run, how to deploy, architecture at a glance.
- **ADRs in `docs/adr/`** — every significant decision gets a numbered record (context, options,
  decision, consequences). Propose a new ADR whenever you make a call that a future reader
  would otherwise have to reverse-engineer.
- **XML doc comments on every public member.** In the metrics engine the comment MUST state the
  formula and cite its source (Epley 1985; Schoenfeld et al. on weekly hard sets; Banister
  TRIMP; Coggan on aerobic decoupling). If a number can't be traced to a source, it doesn't
  belong in the engine.
- **Inline comments at genuinely non-obvious logic** — FIT quirks, deduplication, timezone
  handling, HR-dropout compensation. Not on `i++`.
- **Prompts are code.** They live in the repo, are versioned, and carry a comment explaining
  the reasoning behind their constraints.

## Security

- No secrets in code, images, or config. Key Vault for the Garmin password; Managed Identity
  for SQL and Blob; Entra ID for Foundry. No API keys anywhere.
- Least privilege on every identity. The collector writes to one blob container and reads one
  secret — nothing more.
- No public network access to SQL. TLS enforced. Encryption at rest by default.
- The LLM never receives credentials. Tool outputs are data, not instructions.
- Validate everything crossing a boundary, including LLM output before it reaches a tool.
- Pin the Python collector's dependencies — it's the largest supply-chain surface.

## Testing

- Metrics engine: 100 % coverage, fixture-based tests from real FIT files. Tests first.
- Ingest: golden-file tests (FIT in, expected entities out).
- Agent: the eval harness (scenarios as DB snapshots, assert on plan properties, never on text).

## iOS constraints (always consider in the frontend)

- Web push only on iOS 16.4+ and only when the PWA is added to the home screen — onboarding
  must explain this or notifications silently never arrive.
- Background Sync API is NOT supported by Safari → the offline queue (IndexedDB) syncs on app
  open and network change, never in the background.
- Gym logging must be usable in 10 seconds between two sets. Big targets, prefilled values,
  no modals.

## Project structure

```
src/
  TrainingCoach.Web/          Blazor PWA + API
  TrainingCoach.Domain/       Entities, domain logic
  TrainingCoach.Ingest/       IActivitySource, FIT parsing, dedup
  TrainingCoach.Metrics/      Metrics engine (documented, 100% tested)
  TrainingCoach.Interpretation/ LLM session interpretation
  TrainingCoach.Agent/        Tool loop, tool definitions, prompts
  TrainingCoach.Functions/    Azure Functions (blob trigger, timers)
  garmin-collector/           Python container (GarminDB, isolated)
infra/                        Bicep
tests/
docs/
  spec.md
  adr/
```

## Commands

```bash
dotnet build
dotnet test
dotnet run --project src/TrainingCoach.Web
az deployment group create -g <rg> -f infra/main.bicep
```

## Ways of working

- For anything non-trivial: plan mode first, show the plan, then implement.
- Small vertical slices. One feature = one PR.
- If the spec is unclear, ask — don't guess.
- When you make a decision the spec didn't cover, write an ADR for it.
