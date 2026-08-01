# TrAIning

> **Status: Phase 1 (walking skeleton), in progress.** An empty, PWA-installable Blazor Web App
> builds and runs locally; it doesn't deploy itself yet. See [Status](#status) below.

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

Phase 1 (walking skeleton) is in progress: the Blazor Web App scaffold exists, builds, and is
installable as a PWA. Containerization, Azure infra (Bicep), and CI/CD are still ahead — once
those land, the app deploys itself on every push. See [docs/spec.md §12](docs/spec.md#12-phases)
for the full phased build-out plan.

## Stack

- .NET 10 (LTS), C# — except one isolated Python container (Garmin collector)
- Blazor Web App as a PWA
- ASP.NET Core Web API, EF Core → Azure SQL
- Azure Container Apps, Container Apps Jobs, Functions, Blob Storage, Key Vault
- Claude via Microsoft Foundry (Entra auth)
- Google Calendar API for scheduling
- Bicep for IaC, GitHub Actions for CI/CD

## How to run

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
  TrAIning.Web/            Blazor PWA + API                          ← exists
  TrAIning.Domain/         Entities, domain logic                    (planned)
  TrAIning.Ingest/         IActivitySource, FIT parsing, dedup       (planned)
  TrAIning.Metrics/        Metrics engine (documented, 100% tested)  (planned)
  TrAIning.Interpretation/ LLM session interpretation                (planned)
  TrAIning.Agent/          Tool loop, tool definitions, prompts      (planned)
  TrAIning.Functions/      Azure Functions (blob trigger, timers)    (planned)
  garmin-collector/             Python container (GarminDB, isolated) (planned)
infra/                          Bicep                                 (planned)
tests/                                                                 (planned)
docs/
  spec.md
  adr/
```

(Only `src/TrAIning.Web/` exists so far — see Status.)
