# Training Coach – Requirements & Architecture

**Version:** 3.0 · **Date:** July 2026
**Stack:** .NET 10 (LTS) / Blazor / Azure / Claude via Microsoft Foundry

---

## 1. What this is

A personal training coach that plans on its own, and listens when you have something to say.

The system continuously ingests everything recorded by a Garmin watch — gym sessions, runs, rides, padel, football, circuits — measures what actually happened, and lets an AI agent turn that into a training plan. **This works without any input from you.** If you never write a single message, the app still ingests, measures, interprets, plans, and fills your calendar.

Chat is an optional steering layer on top of an otherwise autonomous system. When you *do* say something — "knee is bothering me", "only Tuesday this week", "why did you put intervals there?" — the plan adapts.

It plans on four inputs:

1. **Training history** — what you actually did, measured from the raw device data
2. **Conversation** *(optional)* — what you tell it, if you tell it anything ("legs are wrecked", "only Tuesday and Thursday this week", "no motivation for running right now")
3. **Goals** — what you're training for (build muscle, get faster, stay healthy), with priorities
4. **Nutrition** *(optional)* — loosely tracked, mentioned in chat, factored in when relevant

It explains its reasoning, answers questions about your training, and writes the planned sessions straight into your calendar.

### Delivery: a PWA

The client is a Progressive Web App — a web app that installs to the iPhone home screen and behaves like a native app (own icon, no browser chrome, push notifications, offline capability), but is built and deployed like a website. No App Store, no review process, no Swift. One codebase in Blazor, deployed from the same pipeline as everything else.

Practical consequence: gym logging works without signal in the basement, and the agent can push a notification to the lock screen.

### Learning objectives (the actual purpose of this project)

| Gap | Closed by |
|---|---|
| Cloud / deployment | Container Apps, Container Apps Jobs, Functions, Bicep, GitHub Actions, Managed Identity |
| Agentic AI | Tool loop with Claude, multi-turn conversation, autonomous replanning |
| LLM Ops | Interpretation pipeline, agent logging, cost tracking, eval harness |
| Azure ecosystem | Microsoft Foundry, Azure SQL, Blob Storage, Key Vault, App Insights, Entra ID |
| Architecture | Provider abstraction, isolated collectors, swappable data sources |

---

## 2. Core principles (non-negotiable)

**1. The LLM interprets and builds. Deterministic code measures.**
The metrics engine measures — from raw device data, with formulas that are documented, tested, and reproducible. The LLM interprets those measurements and builds plans from them. It never computes a number it could be given instead.

**2. Data sources are replaceable and isolated.**
The Garmin collector is an unofficial, fragile fetcher. It runs in its own container, delivers only raw files, and knows nothing about the domain model. If it breaks, the system keeps running on the data it already has.

**3. The agent is autonomous by default, steerable on demand.**
It plans without being asked. It does not require conversation to function, and it does not interrogate you on a fixed rhythm. But anything you tell it changes the plan — chat is a control surface, not a prerequisite.

---

## 3. Data source

### GarminDB (primary, and for now the only one)

A Python tool (GPL-2.0) that authenticates against Garmin Connect via SSO and reads its internal JSON endpoints. Not HTML scraping — it uses the same private API the Connect web app uses.

**What it gives us:**
- The raw **FIT files** of every activity — with laps, per-second records (HR, pace, cadence, power, altitude) and, for strength sessions, the set-level messages the FR255 records automatically
- Daily wellness JSON — sleep, resting HR, stress, all-day HR, body battery, HRV status, weight

This is strictly more data than Strava would ever hand over. Strava's read API gives summaries; the FIT file gives the whole recording.

**What we use it for:** only the `--download` stage. Its SQLite schema is deliberately ignored.

**Risks, stated plainly:**
- Unofficial. Garmin can change the internal API at any time and the collector stops working.
- Requires the Garmin Connect password (Key Vault, never in the image). No 2FA on this account, so login can be automated.
- Pull-based. No webhook — a nightly cron job.

### Strava (fallback, not built yet)

Officially supported OAuth + webhooks, but the data is shallower. Kept as a documented fallback in case the Garmin collector dies permanently.

**Design consequence:** the ingest layer sits behind an `IActivitySource` abstraction from day one. Swapping in Strava must mean writing one new implementation, not touching the domain. This is the one abstraction that is justified up front, because the second implementation is a known requirement, not a speculative one.

---

## 4. Architecture

```
Garmin Collector (Python container, nightly cron job)
  │  garmindb_cli.py --download --latest
  ▼
Azure Blob Storage  ── raw FIT + wellness JSON
  │
  ▼
Ingest Function (C#, blob trigger)          ← IActivitySource implementation
  │  FIT SDK parsing
  ├─► Activity            (common core)
  ├─► ActivityLap         (intervals, work/rest structure)
  ├─► ActivitySample      (time series: HR, pace, cadence, power)
  ├─► StrengthSet         (exercise, set, reps, weight, rest)
  └─► DailyWellness       (sleep, RHR, stress, HRV)
                    │
                    ▼
        ┌───────────────────────────┐
        │      Azure SQL            │
        └───────────────────────────┘
             │                  │
             ▼                  ▼
   Metrics Engine (C#)    Interpretation Function (C#)
   deterministic,         Claude Haiku, once per activity
   documented, tested     → SessionInterpretation
             │                  │
             └────────┬─────────┘
                      ▼
              Coach Agent (Claude via Foundry, tool loop)
                      │
      ┌───────────────┼───────────────┬──────────────────┐
      ▼               ▼               ▼                  ▼
  Chat (PWA)     Web Push     Google Calendar      Plan in DB
```

### The Garmin Collector

Deliberately dumb. An Azure Container Apps Job on a nightly cron (scale-to-zero, cost ≈ 0) that:
1. runs `garmindb_cli.py --download --latest`
2. copies the resulting raw files to Blob Storage
3. exits

No parsing, no schema, no logic. Everything downstream is C#. The GPL-2.0 license stays contained in its own container (separate process, no linking).

If Garmin changes something, exactly one container breaks — and it breaks loudly, without corrupting anything.

---

## 5. Data model

Heterogeneous training does not fit one flat table. A 5×5 squat session and a threshold interval run share almost nothing except a start time. So: a common core, plus typed detail.

### Activity — the common core
```
Id, Source, SourceId, SportType, SubSport, Name,
StartTimeUtc, LocalTimezone, DurationSec, MovingTimeSec,
Distance, Calories, DeviceName,
AvgHr, MaxHr,                    -- summary only; the truth is in ActivitySample
HasSamples, HasSets, HasLaps,    -- which detail tables are populated
RawFileUri,                      -- pointer to the FIT file in Blob
DedupKey, IngestedAt
```

Deliberately thin. Everything sport-specific lives in the detail tables. Table-per-type, not a wide table full of nulls.

### ActivitySample — the time series
```
ActivityId, OffsetSec,
Hr, Speed, Cadence, Power, Altitude, DistanceCum
```
Per-second records from the FIT file. This is what makes interval analysis, time-in-zone, and cardiac drift possible — none of which you can compute from an average heart rate.

*Storage note:* ~3600 rows per hour of training. At 6 h/week that's ~1M rows/year — trivial for Azure SQL's 32 GB free tier. If it ever becomes a problem, samples move to Blob (Parquet) and only derived metrics stay in SQL. Not a problem yet, so not solved yet.

### ActivityLap — structure
```
ActivityId, LapIndex, StartOffsetSec, DurationSec, Distance,
AvgHr, MaxHr, AvgSpeed, AvgPower, LapTrigger, Intensity (active|rest)
```
This is where intervals become visible: 6 × 800 m with 90 s rest is six work laps and six rest laps, not one 10 km run.

### StrengthSet — resistance training
```
ActivityId, SetIndex, ExerciseCategory, ExerciseName,
Reps, WeightKg, DurationSec, RestAfterSec, StartOffsetSec,
AvgHr, WasDetected (bool)        -- watch auto-detection vs. manual correction
```
Structurally nothing like a run, so it gets its own table. Watch rep-detection is imperfect; `WasDetected` marks what came from the device so corrections in the PWA are traceable.

### DailyWellness
```
Date, SleepMinutes, SleepScore, DeepSleepMin, RemSleepMin,
RestingHr, StressAvg, BodyBattery, HrvStatus, HrvMs, WeightKg
```

### SessionInterpretation — what the LLM adds (see §7)

### Conversation, Message — the chat is first-class
```
Message: Id, ConversationId, Role (user|assistant|tool),
         Content, ToolCalls (JSON), CreatedAt, AgentRunId
```
The conversation *is* an input to planning. It gets stored, summarized, and fed back.

### Athlete configuration — three tables, three owners

The distinction matters: what *you* configure, what *changes over time*, and what the *agent believes*. Collapsing these into one profile table is the mistake that quietly ruins the data.

#### AthleteProfile — user-owned, configurable, stable
```
Id (singleton), BirthDate, Sex, HeightCm,
HrMax, HrMaxSource (measured|estimated),   -- Tanaka estimate as default, override when tested
HrZones (JSON),                            -- derived, or manually set
TrainingAge, EquipmentAccess (JSON),
WeeklyTimeBudgetHours, SleepTargetHours,
Preferences, Dislikes, Units, UpdatedAt
```
Edited on a settings page in the PWA. **The agent may not write here.** Store the birth date, not the age — then it never goes stale.

`HrMaxSource` is not cosmetic: it tells the metrics engine how much to trust the zone boundaries. An estimated HRmax makes time-in-zone a rough signal; a measured one makes it a real one.

#### BodyMeasurement — a time series, not a profile field
```
Date, WeightKg, BodyFatPct, MuscleMassKg, Source (garmin|manual)
```
Weight and body composition change. Putting them in the profile means overwriting your own history on every update — and the history is exactly what the coach needs ("weight flat for 8 weeks, but the goal is mass"). A state is not a trajectory. Same mistake class as storing only average heart rate.

Comes in automatically from a Garmin scale via the collector; manually editable.

#### Injury — structured, because the agent has to reason with it
```
Id, BodyPart, Description, OnsetDate, ResolvedDate,
Status (active|resolved|recurring), Severity,
Constraints (JSON),           -- e.g. "no deep knee flexion under load"
Notes, Source (user|agent), CreatedAt
```
Free text in a profile field is something the agent can only *hope* to honour. A structured constraint is something it can be held to — and something the eval harness can assert on.

### Goal
```
Id, Description, Type (hypertrophy|speed|endurance|health|skill),
Priority, TargetDate, TargetMetric, Active,
Source (user|agent), CreatedAt
```
Editable in the UI **and** settable from chat ("I want a sub-20 5k by autumn" creates a goal).

### AgentMemory — what the agent has learned, kept separate
```
Id, UpdatedAt, Summary,          -- rolling LLM-maintained summary
Facts (JSON), Provenance
```
Compressed context so the agent doesn't need the full history in every prompt.

**The boundary is strict:** the agent may create goals and injuries (marked with `Source = agent`), but it may never silently rewrite `AthleteProfile`. The user must always be able to see what the system *believes* about them, separately from what they *told* it. Machine-written memory and human-authored configuration are different kinds of truth and are stored as such.

### NutritionNote (optional, low-friction)
```
Id, Date, FreeText, InterpretedJson, Source (chat|manual)
```
No calorie tracking. You mention it in chat, the LLM interprets it, the agent factors it in when it's relevant (e.g. "you've mentioned eating badly three times this week and you're trying to build muscle").

### Availability
```
Id, ValidFrom, ValidTo, DayOfWeek, StartTime, EndTime, Note
```

### PlanItem
```
Id, PlannedDate, TimeWindow, SessionType, Prescription (JSON),
Rationale, Status (proposed|accepted|done|skipped|replanned),
CalendarEventId, LinkedActivityId, CreatedByRunId, SupersededById
```
Plans are versioned, not overwritten. When the agent replans, the old item is superseded — so you can see *why* the week changed.

### AgentRun
```
Id, StartedAt, Trigger, Model, ToolCalls (JSON),
TokensIn, TokensOut, CachedTokens, CostEur, Outcome, ErrorMessage
```

---

## 6. Metrics Engine (deterministic, documented, tested)

This is the only code that computes numbers. Every formula carries an XML doc comment with a reference to the literature it comes from. 100 % test coverage, no exceptions.

### Cardio (from ActivitySample + ActivityLap)
- **Time in HR zones** — per session and rolling, from the actual HR trace, not the average
- **Interval structure** — work/rest laps, work duration, recovery duration, HR at the end of each rep
- **Heart-rate recovery (HRR)** — HR drop in the 60 s after a work interval. A well-established fitness marker.
- **Aerobic decoupling** — pace-to-HR drift between the first and second half of a steady effort (Pa:HR). Rising decoupling means the aerobic base isn't holding.
- **Session load** — HR-weighted (TRIMP-style, Banister/Edwards); documented with the exact weighting used
- **Efficiency trend** — speed at a given HR over time; the cleanest signal that endurance is actually improving

### Strength (from StrengthSet)
- **Tonnage** — Σ (reps × weight), per session, per exercise, per muscle group
- **Hard sets per muscle group per week** — the single best-supported driver of hypertrophy in the literature (Schoenfeld et al.). If the goal is muscle, this is *the* number.
- **Estimated 1RM** — Epley and Brzycki, both computed, divergence flagged
- **Progression & stagnation** — trend per exercise over an N-week window; explicit stagnation flag
- **Set/rep/rest profile** — was this a strength session (low reps, long rest) or a hypertrophy session (moderate reps, short rest)? Derived, not guessed.
- **PR detection** — per exercise, per rep range

### Recovery (from DailyWellness)
- **RHR baseline deviation** — rolling z-score against a 30-day baseline. A single resting HR value is meaningless; a deviation from your own baseline is not.
- **Sleep debt** — rolling deficit against a configured target
- **HRV trend** — direction and stability, not the absolute number

### Load management
- **Rolling load** — 7 / 14 / 28-day windows, weighted by session load
- **Days since load, per muscle group and per energy system**
- **Ramp rate** — how fast load is increasing week over week

Explicitly *not* used: ACWR and Foster monotony. Both come from single-sport elite settings with homogeneous load and don't survive contact with a training mix that includes padel and five-a-side. This decision goes in an ADR.

---

## 7. Interpretation (the LLM layer)

**What "interpretation" means here, concretely:** the metrics engine can tell you that a session had 42 minutes in zone 4, six work laps, and an HRR of 28 bpm. It cannot tell you that this was a threshold session, that it was harder than intended because you'd slept badly, or that it competes with tomorrow's leg day. That translation — from measurements to *meaning* — is the LLM's job.

Runs once per activity, triggered when ingest completes. Result is persisted and never recomputed.

**Model:** Claude Haiku 4.5. High volume, bounded task.

**Input:** the full metric set for the session (not the raw samples), the athlete profile, active goals, recent wellness, and the last few sessions.

**Output — `SessionInterpretation`:**
```jsonc
{
  "session_type": "threshold_run",           // free-ish label, from a controlled vocabulary
  "primary_stimulus": "lactate_threshold",   // what this session actually trained
  "secondary_stimuli": ["aerobic_base"],
  "execution_quality": {
    "score": 1-10,                           // did the session do what it looked like it was for?
    "notes": "HR drifted in reps 5-6, likely under-recovered"
  },
  "systemic_fatigue": 1-10,                  // whole-body / CNS cost
  "local_fatigue": {                         // per muscle group, 0-10
    "quads": 7, "hamstrings": 4, "calves": 6
  },
  "energy_systems": ["aerobic", "anaerobic_lactic"],
  "goal_alignment": [
    { "goal_id": "...", "contribution": "high|medium|low|counterproductive",
      "why": "one sentence" }
  ],
  "recovery_demand_hours": 36,
  "data_quality": {
    "issues": ["hr_dropout_at_12min"],       // honest about bad data
    "confidence": "low|medium|high"
  },
  "notable": "First time holding 4:10/km for 6 reps.",
  "questions_for_athlete": [                 // feeds the agent's follow-up
    "Was rep 5 harder than it should have been?"
  ],
  "rationale": "two sentences, why this interpretation"
}
```

Note `questions_for_athlete` — this is how the interpretation layer hands work to the agent. It's the mechanism behind "ask a question after a session when there's something worth asking about, and stay quiet when there isn't."

**Rules the prompt enforces:** never compute a number you were given; if the data is bad, say so rather than inventing an interpretation; set confidence honestly.

---

## 8. The Coach Agent

**Model:** Claude Sonnet/Opus via Foundry. Messages API, tool use, prompt caching on the system prompt and athlete profile (this is the main cost lever).

### Behaviour

**Plans autonomously.** Every Sunday evening it drafts next week from data alone — history, metrics, wellness, goals — and presents it as a *proposal*. This is the default mode and requires nothing from the user.

**Replans when you say something.** Optional, but this is where the system gets good. You write:
- "My knee is bothering me" → it pulls leg volume, proposes alternatives, adjusts the week
- "I can only train Tuesday and Saturday this week" → it re-prioritizes against your goals and rebuilds
- "I want to hit a 20:00 5k by autumn" → it creates a goal and reshapes the block
- "No motivation for running right now" → it asks whether to substitute or reduce, then adapts

The plan is a living artifact. It exists whether or not you talk to it, and it responds when you do. It is never silently overwritten — superseded items stay visible with their reasoning.

**The primary surface is the plan, not the chat.** The app opens on this week's sessions and your metrics. Chat is one tap away, not the front door.

**Speaks up when it should, and otherwise doesn't.** Push notification triggers:
| Trigger | Behaviour |
|---|---|
| Sunday evening | "Here's next week — have a look." |
| 5 days without any conversation | A single nudge. Not a nag; one message. |
| The agent genuinely needs input | It asks. (e.g. `questions_for_athlete` came back non-empty on a notable session) |
| After a session is ingested | *Optionally* a short reaction, a question, and a replan of the rest of the week — only when the session diverged from the plan or something is worth saying. |
| Never | Anything else. Silence is the default. |

### Tools

| Tool | Purpose |
|---|---|
| `get_metrics(window, filters)` | Everything from the metrics engine |
| `get_activities(from, to, detail)` | Sessions with interpretations; optionally laps/sets |
| `get_exercise_history(exercise)` | Progression, e1RM, stagnation |
| `get_wellness(from, to)` | Sleep, RHR baseline deviation, HRV trend |
| `get_goals()` / `set_goal(...)` | Read and create goals from conversation |
| `get_availability()` / `set_availability(...)` | Read and update from conversation |
| `get_nutrition_notes(from, to)` | Optional context |
| `get_plan(week)` | Current plan |
| `write_plan(items[])` | Propose a week |
| `update_plan_item(id, changes, reason)` | Replan a single session (supersedes, never deletes) |
| `upsert_calendar_event(planItemId)` | Google Calendar API — create, move, or cancel |
| `push_notification(text)` | Reach the athlete |
| `update_athlete_profile(patch)` | Maintain long-term memory |

### Calendar

Accepted plan items are written to **Google Calendar** via the Google Calendar API. It syncs to iOS natively, so sessions show up on the phone without any extra work.

- **Auth:** OAuth 2.0, one-time consent, refresh token in Key Vault. No service account — this is a personal calendar, not a workspace one.
- **A dedicated "Training" calendar**, not the main one. Keeps the agent's writes isolated and makes it trivial to wipe everything if a replanning bug goes wrong.
- **Idempotent upsert.** `CalendarEventId` on `PlanItem` links the two. Replanning moves or rewrites the event; a superseded item's event is cancelled. Never create a duplicate — always upsert against the stored ID.
- **One-way sync (app → calendar).** Reading changes back from the calendar is deliberately out of scope: availability is communicated in chat, not by moving events around. If that turns out to be annoying in practice, revisit it — but don't build a bidirectional sync speculatively.
- The event body carries the agent's rationale, so the *why* is visible on the phone without opening the app.

Google is the one external dependency besides the Garmin collector. It sits behind an `ICalendarSink` interface — not because a second implementation is planned, but because it's an external boundary, and that's exactly where dependency inversion earns its keep.

---

## 9. iOS constraints (designed in from the start)

- **Web push** works only on iOS 16.4+ **and only** when the PWA is added to the home screen → an onboarding step in the app must explain this, or notifications silently never arrive.
- **Background Sync API** is not supported by Safari → the offline gym queue (IndexedDB) syncs on app open and on network change, never in the background.
- Gym logging must be usable in 10 seconds between two sets. Big targets, last values prefilled, no modal dialogs.

---

## 10. Azure resources & cost

| Component | Service | Cost |
|---|---|---|
| API + Blazor PWA | Container Apps (scale-to-zero) | ~0 € (free grant) |
| Garmin collector | Container Apps Job (nightly cron) | ~0 € |
| Database | Azure SQL, free tier (32 GB) | 0 € |
| Raw FIT/JSON files | Blob Storage (cool tier) | < 1 € |
| Ingest, interpretation, timers | Azure Functions (consumption) | ~0 € |
| LLM | Claude in Microsoft Foundry | 3–8 € |
| Container images | GitHub Container Registry | 0 € (avoids ACR) |
| Monitoring | Application Insights (free tier) | 0 € |
| Secrets | Key Vault | < 1 € |
| Auth | Entra ID (single user) | 0 € |
| **Total** | | **≈ 4–10 €/month** |

**On LLM billing:** a Claude Pro subscription cannot be used here. Pro covers the consumer chat interface and includes no API access — there is no way to route application traffic through it. Programmatic access is always per-token, via the Anthropic API or via Foundry. Foundry is chosen because it keeps auth (Entra), billing, and governance inside Azure, which is itself one of the learning objectives.

**Cost scales with conversation, not with training.** Baseline running cost is low and predictable: one Haiku interpretation per session, one planning run per week. Chat is what varies — talk a lot in a week and that week costs more. Prompt caching is the main lever: the system prompt, athlete profile, and goal set are stable across turns, so cache them.

**Foundry prerequisite:** an Azure subscription with a real payment method. Student, trial, or credit-only subscriptions will not work.

---

## 11. Phases

### Phase 0 – Week 0: Reconnaissance (no production code)
- Run GarminDB locally: `pip install garmindb`, configure, `garmindb_cli.py --all --download`
- **Open a FIT file from a gym session and confirm the set messages are there.** This validates the entire data model.
- Parse one FIT file with the FIT SDK for .NET — confirm you can read records, laps, and sets
- Check the Azure subscription is pay-as-you-go (Foundry prerequisite)

### Phase 1 – Weeks 1–2: Walking skeleton
Empty Blazor PWA, installable on iOS. Docker. Bicep (resource group, Log Analytics, Container Apps Environment, Azure SQL, Blob, Key Vault). GitHub Actions.
**Milestone: the app is live at a URL and deploys itself on git push.** Nothing works yet. That's fine — this is the step the whole project exists for.

### Phase 2 – Weeks 3–4: Ingest
Garmin collector as a Container Apps Job. Blob-triggered ingest function. FIT parsing into Activity / Lap / Sample / StrengthSet / DailyWellness. `IActivitySource` abstraction in place. Raw session list in the PWA.

### Phase 3 – Weeks 5–6: Measurement
The metrics engine, with tests and documented formulas. A dashboard that shows time-in-zone, tonnage, hard sets per muscle group, RHR deviation. **At this point the app is already useful, before any AI is involved.** That's a deliberate checkpoint: if the numbers aren't right, no LLM will save you.

### Phase 4 – Weeks 7–8: Interpretation
The interpretation function (Haiku). `SessionInterpretation` persisted. Interpretations visible per session in the UI. Goals and availability, editable.

### Phase 5 – Weeks 9–11: The agent
Tool loop in C#. **Autonomous weekly planning first** — the agent should produce a sensible week from data alone before a chat box exists. Then the chat UI and replanning from conversation on top. `AgentRun` logging with cost tracking. Athlete profile with rolling summarization.

Build it in that order deliberately: if the agent can't plan well without being talked to, chat will just be a way to paper over a weak planner.

### Phase 6 – Weeks 12–13: Reach
Web push (VAPID) with the notification rules from §8. Google Calendar integration (OAuth, dedicated training calendar, idempotent upsert). Nutrition notes.

### Phase 7 – Week 14+: Rigor
Eval harness. Offline gym logging. Strava fallback source (proves the abstraction was real).

---

## 12. Eval harness (not optional)

Scenarios as database snapshots that the agent runs against. Assert on *properties* of the plan, never on exact text.

| Scenario | Expected behaviour |
|---|---|
| Three hard sessions in four days, poor sleep, RHR elevated | Proposes recovery, doesn't add load |
| "I'm sick, 39 °C" | Cancels everything, doesn't negotiate |
| Only two slots available this week | Prioritizes by goal priority, drops the rest |
| Squat unchanged for 6 weeks, goal is hypertrophy | Notices stagnation, changes the stimulus |
| No activity or conversation for 10 days | Asks, doesn't guess |
| Collector down, no wellness data for 3 days | Plans anyway, states the uncertainty |
| Goal is speed, but the user only wants to lift | Surfaces the conflict honestly instead of pleasing |
| User says "my knee hurts" | Reduces knee-loading volume, offers alternatives, does not diagnose |

Scoring: partly programmatic (does the plan have property X), partly LLM-as-judge with a rubric.

**This is the part almost nobody builds, and exactly the part worth talking about in an interview.**

---

## 13. Engineering conventions

### Design
- **SOLID throughout.** Especially Dependency Inversion at the ingest boundary (`IActivitySource`) and Single Responsibility in the metrics engine — one calculator per metric family, not a god class.
- **Abstract where a second implementation is known or the boundary is external.** `IActivitySource` is justified (Strava is a planned second implementation). A generic `IRepository<T>` over EF Core is not. No speculative abstraction — the second occurrence earns the interface, not the first.
- **Patterns are welcome where they carry weight:** Strategy for metric calculators, Adapter at the source boundary, Chain of Responsibility for the ingest pipeline, Command for agent tool invocations, Memento-ish versioning for superseded plan items. Use them when they name something real; don't decorate.

### Documentation (explicitly wanted, not an afterthought)
- **README.md** — what it is, how to run it, how to deploy it, architecture at a glance
- **ADRs** in `docs/adr/` — every significant decision gets a numbered record: context, options, decision, consequences. Known ADRs already: *ADR-001 GarminDB over Strava as primary source*, *ADR-002 Metrics computed deterministically, not by the LLM*, *ADR-003 No ACWR / Foster monotony for heterogeneous training*, *ADR-004 Claude via Foundry rather than the Anthropic API*, *ADR-005 Table-per-type for activity detail*, *ADR-006 Google Calendar as a one-way sink*.
- **XML doc comments on every public member.** For anything in the metrics engine, the comment must state the formula and cite its source (e.g. Epley 1985; Schoenfeld et al. on weekly hard sets; Banister TRIMP; Coggan on aerobic decoupling). If a number can't be traced to a source, it doesn't belong in the engine.
- **Inline comments at genuinely non-obvious logic** — FIT quirks, deduplication rules, timezone handling, HR-dropout compensation. Not on `i++`.
- **Prompt files are documented artifacts**, versioned in the repo with the reasoning behind them. Prompts are code.

### Security
- No secrets in code, images, or config files. Key Vault for the Garmin password; Managed Identity for SQL and Blob; Entra ID for Foundry. No API keys anywhere.
- Least privilege on every managed identity. The collector can write to one blob container and read one secret — nothing else.
- Encryption in transit and at rest by default; TLS enforced; no public network access to SQL.
- The LLM never receives credentials, and tool outputs are treated as data, not instructions.
- Input validation at every boundary, including anything that came out of the LLM before it reaches a tool.
- Dependency scanning in CI. The Python collector is the largest supply-chain surface — pin it.

### Testing
- Metrics engine: 100 % coverage, with fixture-based tests from real FIT files.
- Ingest: golden-file tests (FIT in, expected entities out).
- Agent: the eval harness in §12.

---

## 14. Open questions

1. **Sample retention:** keep per-second samples in SQL indefinitely, or roll them to Blob after N months? Deferred until it hurts.
2. **Strength exercise vocabulary:** the FIT SDK's exercise enum vs. a custom taxonomy. Affects muscle-group attribution.
3. **How opinionated should the coach be?** A coach that always agrees with you is useless. Where's the line between adaptive and spineless? This is a product decision, and it belongs in the system prompt.
