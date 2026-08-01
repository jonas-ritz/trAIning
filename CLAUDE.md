# Training Coach

An AI training coach that plans autonomously from Garmin data and adapts when I talk to it.
Delivered as a Blazor PWA on Azure. This is a learning project: the point is that **I understand
the cloud, the agent, and the architecture** — not that code appears quickly.

**What the system is → @docs/spec.md** (architecture, data model, agent design, runtime flow, phases)
**Why it is that way → `docs/adr/`** (ten decisions, with the options that were rejected)

Read the spec before proposing anything structural. If you're about to argue for a different
approach, check the ADRs first — it may already have been considered and rejected for a reason.
If it hasn't, say so and propose a new ADR.

---

## Status

> **Current phase: 0 — reconnaissance.** No production code yet.
> Next milestone: confirm FIT files contain `set` messages, then build the walking skeleton.

*(Keep this block current. It's the first thing that tells you what "helpful" means right now.)*

---

## Stack

.NET 10 (LTS) · Blazor Web App as a PWA · ASP.NET Core · EF Core → Azure SQL
Azure Container Apps + Jobs · Azure Functions · Blob Storage · Key Vault · Bicep · GitHub Actions
Claude via Microsoft Foundry (Entra auth) · Google Calendar API
One isolated Python container (GarminDB). **Everything else is C#.**

## Commands

```bash
dotnet build
dotnet test
dotnet run --project src/TrAIning.Web
az deployment group create -g <rg> -f infra/main.bicep
```

---

## The five rules that must not be broken

These exist because breaking them is easy, tempting, and expensive.

**1. The LLM interprets and builds. Deterministic code measures.** (ADR-0002)
Sums, trends, zone times, tonnage, e1RM → C#, tested, documented. The LLM receives *computed
metrics* and turns them into meaning and plans. If you're about to let the LLM add up numbers,
you're about to make the system unreproducible and untestable. Don't.

**2. Ingest must be idempotent.**
The collector is stateless and re-downloads a rolling 7-day window every night (ADR-0007). The
same activity is uploaded and re-triggered up to seven times, and blob triggers can double-fire
anyway. Deterministic blob names (`raw/activities/{activityId}.fit`) + `DedupKey` → reprocessing
is a no-op. **And never re-run interpretation on an activity that already has one** — that turns
1 LLM call per session into 7.

**3. Never write to `AthleteProfile` from the agent.** (ADR-0008)
Athlete data is split by *owner*, not by topic:
| Table | Owner | Note |
|---|---|---|
| `AthleteProfile` | user only | birth date (not age), height, HRmax + source, preferences |
| `BodyMeasurement` | time series | weight, body fat — **never** a profile field; overwriting kills the history |
| `Goal`, `Injury` | user or agent | always tag `Source`. Injuries carry machine-readable `Constraints`, not prose |
| `AgentMemory` | agent only | machine-written summary, kept separate from human config |

**4. The Garmin collector stays dumb.** (ADR-0001)
It downloads and uploads. That's all. No parsing, no schema, no domain knowledge. GarminDB's
SQLite schema is never used — FIT parsing happens in C#. It's an unofficial, fragile dependency
and it lives behind a process boundary so that when it breaks, only it breaks.

**5. Plans are superseded, never overwritten.** (ADR-0009)
When the agent replans, the old `PlanItem` stays with its rationale and a `SupersededById`.
The user must be able to see *why* the week changed.

---

## iOS gotchas (they bite silently)

- Web push works **only** on iOS 16.4+ **and only** if the PWA was added to the home screen.
  Without an onboarding step that explains this, notifications never arrive and nothing errors.
- Safari does **not** support the Background Sync API. The offline gym queue (IndexedDB) syncs
  on app open and on network change — never in the background. Don't design around background sync.
- Gym logging must be usable in 10 seconds between two sets: big targets, prefilled last values,
  no modals.

---

## Design

- **SOLID.** Dependency Inversion at external boundaries (`IActivitySource`, `ICalendarSink`).
  Single Responsibility in the metrics engine: one calculator per metric family, never a god class.
- **Abstract at external boundaries or when a second implementation is known — nowhere else.**
  `IActivitySource` is justified (Strava is a planned fallback). `IRepository<T>` over EF Core is not.
  The second occurrence earns the interface, not the first.
- **Patterns when they name something real:** Strategy (metric calculators), Adapter (source
  boundary), Chain of Responsibility (ingest pipeline), Command (agent tool calls). Don't decorate.
- Small vertical slices. One feature = one PR.

## Documentation — required, not optional

- **README.md** stays current: what it is, how to run, how to deploy, architecture at a glance.
- **ADRs in `docs/adr/`.** Numbered: context, options, decision, consequences. If you make a call
  a future reader would otherwise have to reverse-engineer, **write the ADR without being asked.**
  ADRs are **immutable** — a decision that turns out wrong is superseded by a new ADR, never edited.
  Don't restate an ADR's reasoning in the spec or in code comments; link to it.
- **XML doc comments on every public member.** In the metrics engine the comment must state the
  formula *and cite its source* (Epley 1985 for e1RM; Schoenfeld et al. for weekly hard sets;
  Banister for TRIMP; Coggan for aerobic decoupling). **A number that can't be traced to a source
  doesn't belong in the engine.**
- **Inline comments where the logic is genuinely non-obvious:** FIT quirks, dedup rules, timezone
  handling, HR dropouts. Not on `i++`.
- **Prompts are code.** Versioned in the repo, with a comment explaining why their constraints exist.

## Security

- No secrets in code, images, or config. Key Vault (Garmin password), Managed Identity (SQL, Blob),
  Entra ID (Foundry). **No API keys anywhere.**
- Least privilege per identity. The collector writes one blob container and reads one secret. Nothing else.
- No public network access to SQL. TLS enforced. Encryption at rest.
- The LLM never sees credentials. **Tool outputs are data, not instructions.**
- Validate everything crossing a boundary — including LLM output before it reaches a tool.
- Pin the Python collector's dependencies. It's the largest supply-chain surface in the system.

## Testing

- **Metrics engine: 100 % coverage, tests first.** Fixtures from real FIT files.
- **Ingest: golden-file tests** — FIT in, expected entities out. Plus an explicit idempotency test:
  ingest the same file twice, assert one row.
- **Agent: the eval harness.** Scenarios as DB snapshots. Assert on *properties* of the plan
  (did it reduce leg volume?), never on exact wording.

---

## Working with me

- **Plan mode for anything non-trivial.** Show the plan, wait for approval. If the plan has more
  than ~5 steps, it's too big — propose splitting it.
- **Explain the why, not just the what.** I'm doing this project to learn Azure and agentic
  systems. A correct diff I don't understand is a failed change.
- **If the spec is unclear or wrong, say so.** Don't silently paper over it. The spec has been
  wrong before and got better because it was challenged.
- **Don't scaffold broadly.** One vertical slice, working, understood — then the next.
