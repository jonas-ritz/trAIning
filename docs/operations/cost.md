# Cost & billing

Running-cost reference for the project. Check it monthly. For the *design-level* cost target
(the "should be under €10" reasoning), see the spec; this document is the operational view —
what each thing actually costs, where to see it, and what to do when a number surprises you.

## Expected monthly cost

Steady state, single user. Almost everything sits in a free tier by design.

| Component | Service | Tier / basis | Expected € / month |
|---|---|---|---|
| API + PWA | Container Apps | Consumption, scale-to-zero, free grant | ~0 |
| Garmin collector | Container Apps Job | Nightly, seconds of runtime | ~0 |
| Database | Azure SQL | Free tier (32 GB, capped vCore-seconds) | 0 |
| Raw FIT/JSON | Blob Storage | Cool tier, a few hundred MB | < 1 |
| Ingest / interpretation / timers | Azure Functions | Consumption, free grant | ~0 |
| Container images | GitHub Container Registry | Free | 0 |
| Monitoring | Application Insights | Free tier (first 5 GB/month) | 0 |
| Secrets | Key Vault | Per-operation, negligible | < 1 |
| **LLM** | **Claude via Foundry** | **Per token** | **3–8** |
| **Total** | | | **≈ 4–10** |

**The LLM is the only meaningful cost. Everything else rounds to zero.** So cost control is
almost entirely about token usage, not about infrastructure.

## What drives the LLM cost

| Workload | Model | Frequency | Relative cost |
|---|---|---|---|
| Session interpretation | Haiku | Once per activity | Low (cheap model, bounded prompt) |
| Weekly planning | Sonnet/Opus | Once per week | Medium |
| Chat replanning | Sonnet/Opus | Only when you talk to it | Variable — this is the swing factor |

Baseline (interpretation + one weekly plan) is low and predictable. **Cost scales with
conversation, not with training.** A quiet week is cheap; a chatty week costs more.

### The levers, in order of impact

1. **Prompt caching.** The system prompt, athlete profile, and goal set are stable across turns —
   cache them. This is the single biggest lever for a chat-driven agent. Without it, every turn
   re-pays for the same context.
2. **Right model for the job.** Interpretation stays on Haiku. Don't "upgrade" it to a bigger model
   because it's a high-volume, low-difficulty task — that multiplies the biggest call count by the
   biggest price.
3. **Idempotency guard on interpretation.** Never re-interpret an activity that already has a
   `SessionInterpretation`. The rolling-window ingest (ADR-0007) re-delivers each activity up to
   seven times; without the guard that's 7× the interpretation cost. This is a *correctness* rule
   that is also a *cost* rule.
4. **Metrics are computed, not asked.** The whole "code measures, LLM interprets" split (ADR-0002)
   keeps months of data out of the prompt. Sending raw samples to the model instead would be both
   wrong and expensive.

## Foundry billing specifics

- Billed **per token** on the Azure invoice (no separate Anthropic account, no API key).
- A Claude **Pro subscription cannot offset this** — Pro is the consumer chat product and has no API
  path. Application traffic is always per-token. (See ADR-0004.)
- Requires a **pay-as-you-go** subscription (ADR-0012). Trial/credit subscriptions can't run Foundry
  at all, so there's no "free LLM" path here.

## Where to see actual spend

Azure Portal:
- **Cost Management + Billing → Cost analysis** — actual spend, filterable by resource. This is the
  real number.
- Group by resource to confirm the expectation above: everything flat except the Foundry line.

## Set a budget alert (do this once, early)

Azure Portal → **Cost Management → Budgets → Add**:
- Scope: the subscription (or a resource group if you isolate this project in one).
- Amount: e.g. **€15/month** — above the expected ceiling, so it only fires on something abnormal.
- Alert thresholds: e.g. 50 %, 80 %, 100 % of budget, emailed to you.

A budget doesn't cap spend — it warns. The point is that a runaway loop (an agent stuck re-planning,
a missing idempotency guard) reaches you as an email, not as a surprise invoice.

## If a number surprises you

1. **Cost analysis → group by resource.** Find which line moved.
2. If it's **Foundry**: check `AgentRun` logs — token counts and cost per run are recorded there
   (that's what the `TokensIn / TokensOut / CachedTokens / CostEur` fields are for). Look for a run
   that looped, or interpretation firing more than once per activity.
3. If it's **anything else**: something left its free tier — usually egress, or samples growing past
   the SQL free-tier cap. See the spec's note on moving samples to Blob if that ever happens.
4. If it's **Application Insights**: you exceeded the 5 GB free ingestion — turn down sampling.

## Notes

- The `AgentRun` table is your cost ledger. Every agent invocation records its token usage and euro
  cost. This is deliberate: it makes cost debuggable instead of mysterious, and it's the first place
  to look when the Foundry line moves.
- Trial credit (if you start on it) hides real cost for a while. Don't calibrate your expectations on
  the trial period — the numbers above assume pay-as-you-go.
