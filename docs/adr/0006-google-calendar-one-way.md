# ADR-0006: Google Calendar as a one-way sink

**Status:** Accepted
**Date:** 2026-07

## Context

Planned sessions should appear in the calendar on the phone. The user lives in Google Calendar.
Microsoft Graph would have fit the Azure learning objectives more neatly, but the calendar people
actually use wins over the calendar that would look tidier in the architecture diagram.

## Options considered

- **Microsoft Graph / Outlook.** Stays inside Entra. But it is not the calendar in daily use.
- **Google Calendar, bidirectional.** The agent writes events; moved events feed availability back.
  Substantial work, and an entire class of sync-conflict bugs.
- **Google Calendar, one-way.**

## Decision

Google Calendar, one-way (app → calendar). Availability is communicated in chat, not by dragging
events around.

## Consequences

- OAuth 2.0, one-time consent, refresh token in Key Vault. Not a service account — this is a
  personal calendar.
- **A dedicated "Training" calendar, not the main one.** If a replanning bug runs amok, the recovery
  is deleting one calendar rather than repairing a life.
- **Idempotent upsert against the stored `CalendarEventId`.** Replanning moves or rewrites the
  event; a superseded plan item cancels its event. Never create a duplicate.
- The event body carries the agent's rationale, so the *why* is visible on the phone without
  opening the app.
- Google is one of only two external dependencies (with GarminDB). It sits behind `ICalendarSink` —
  not because a second implementation is planned, but because it is an external boundary, and that
  is exactly where dependency inversion earns its keep.
- If reading the calendar back turns out to matter in practice, revisit. Do not build it speculatively.
