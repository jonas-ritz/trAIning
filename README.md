# Training Coach

> **Status: planning phase.** No application code exists yet — this repo currently holds the
> spec and working conventions only. See [Status](#status) below.

A personal training coach that plans on its own and listens when you have something to say.

It ingests everything recorded by a Garmin watch, measures what actually happened with a
deterministic metrics engine, and lets an AI agent (Claude, via Microsoft Foundry) plan
training from history, goals, optional conversation, and optional nutrition notes. Chat is an
optional steering layer, not a requirement — the system plans, explains its reasoning, and
writes sessions into Google Calendar with zero user input.

Delivered as a PWA: installs to the iOS home screen, supports web push, and works offline in
the gym. One Blazor codebase, no App Store.

Full requirements and architecture: [docs/spec.md](docs/spec.md).
Working conventions for this repo: [CLAUDE.md](CLAUDE.md).

## Status

Early planning stage — no application code yet. See [docs/spec.md §11](docs/spec.md#11-phases)
for the phased build-out plan, starting with Phase 0 (reconnaissance) and Phase 1 (walking
skeleton).

## Stack

- .NET 10 (LTS), C# — except one isolated Python container (Garmin collector)
- Blazor Web App as a PWA
- ASP.NET Core Web API, EF Core → Azure SQL
- Azure Container Apps, Container Apps Jobs, Functions, Blob Storage, Key Vault
- Claude via Microsoft Foundry (Entra auth)
- Google Calendar API for scheduling
- Bicep for IaC, GitHub Actions for CI/CD

## How to run

No runnable application yet. Once the walking skeleton (Phase 1) lands, this section will
cover local run instructions:

```bash
dotnet build
dotnet test
dotnet run --project src/TrAIning.Web
```

## How to deploy

Deployment is via Bicep + GitHub Actions once infrastructure exists:

```bash
az deployment group create -g <resource-group> -f infra/main.bicep
```

## Architecture at a glance

```
Garmin Collector (Python container, nightly cron)
  → Azure Blob Storage (raw FIT + wellness JSON)
  → Ingest Function (C#, FIT parsing)
  → Azure SQL
  → Metrics Engine (deterministic)  +  Interpretation Function (Claude Haiku)
  → Coach Agent (Claude, tool loop)
  → Chat (PWA) / Web Push / Google Calendar / Plan in DB
```

See [docs/spec.md §4](docs/spec.md#4-architecture) for the full diagram and rationale.

## Project structure

```
src/
  TrAIning.Web/            Blazor PWA + API
  TrAIning.Domain/         Entities, domain logic
  TrAIning.Ingest/         IActivitySource, FIT parsing, dedup
  TrAIning.Metrics/        Metrics engine (documented, 100% tested)
  TrAIning.Interpretation/ LLM session interpretation
  TrAIning.Agent/          Tool loop, tool definitions, prompts
  TrAIning.Functions/      Azure Functions (blob trigger, timers)
  garmin-collector/             Python container (GarminDB, isolated)
infra/                          Bicep
tests/
docs/
  spec.md
  adr/
```

(Directories above are planned; not all exist yet — see Status.)
