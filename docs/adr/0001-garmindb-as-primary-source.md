# ADR-0001: GarminDB as the primary data source, Strava as fallback

**Status:** Accepted
**Date:** 2026-07

## Context

All training is recorded on a Garmin Forerunner 255. Two paths exist to get that data into the system.

Strava offers an official API with OAuth and webhooks, no approval process, and a self-managed
developer tier. But it only exposes *summaries* of activities.

Garmin holds far more: full FIT files with per-second records, lap structure, and — critically —
the set-level messages the FR255 records automatically during strength training. It also holds
sleep, resting HR, stress, Body Battery and HRV, none of which ever reach Strava.

Garmin's official Connect Developer Program is not a realistic path: reports indicate it is
currently suspended to new sign-ups, and even when open it requires a legal entity and a
commercial onboarding process. GarminDB is a third-party Python tool that authenticates via SSO
and reads Garmin Connect's internal JSON endpoints — unofficial, but it works, and it retains the
raw FIT files.

## Options considered

- **Strava only.** Official, robust, webhook-driven. But summary-level data means no interval
  analysis, no set-level strength data, no recovery metrics. The metrics engine would be reduced
  to averages, and the coach would be reasoning on shadows.
- **Garmin Health API.** The correct answer if it were reachable. It is not.
- **GarminDB.** Unofficial and fragile, but delivers everything.

## Decision

GarminDB as the primary and, for now, only source. Strava is kept as a documented fallback in case
the collector breaks permanently.

The data quality difference is decisive: a coach that cannot see intervals, sets, or sleep is not
a coach. Accepting a fragile source is preferable to building on data that is structurally
insufficient.

## Consequences

- **The collector is a known-fragile dependency.** Garmin can change its internal API at any time.
  This is isolated in its own container (see ADR-0007) so that when it breaks, only it breaks.
- Requires the Garmin Connect password (Key Vault). The account has no 2FA, so login can be automated.
- Pull-based, not event-driven. No webhook — a nightly cron job.
- FIT parsing becomes our responsibility, in C#, with the FIT SDK.
- **`IActivitySource` is introduced from day one.** This is the one abstraction justified up front,
  because a second implementation (Strava) is a known requirement, not a speculative one.
- If GarminDB dies permanently, the fallback is a degraded but functioning system on Strava data.
