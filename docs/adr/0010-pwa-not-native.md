# ADR-0010: PWA instead of a native iOS app

**Status:** Accepted
**Date:** 2026-07

## Context

The client runs on an iPhone. It needs to log gym sets (often without signal, in a basement),
show the plan and metrics, host the chat, and receive push notifications.

## Options considered

- **Native iOS (Swift).** Best platform integration — including HealthKit — but a second language,
  a second toolchain, an App Store review cycle, and no shared code with the .NET backend.
- **Blazor PWA.** One language, one repo, one pipeline. Installs to the home screen, runs full
  screen with its own icon, supports offline storage and push.

## Decision

Blazor PWA.

The deciding factor is that this is a learning project about Azure and agentic systems, not about
Swift. Every hour spent on a second toolchain is an hour not spent on the thing the project exists
to teach. And deploying the client from the same pipeline as the backend is itself part of the
lesson.

## Consequences

Three iOS constraints are now **design requirements**, not surprises:

- **Web push requires iOS 16.4+ and only works once the PWA is added to the home screen.** Without
  an onboarding step that explains this, notifications silently never arrive and nothing errors.
  This must be built, not documented and forgotten.
- **Safari does not support the Background Sync API.** The offline gym queue (IndexedDB) syncs on
  app open and on network change — never in the background. Nothing may be designed around
  background sync.
- **The icon is frozen after installation.** iOS does not refresh it on redeploy. Ship a proper
  `apple-touch-icon` (180×180, square, no transparency, no self-rounded corners) the first time,
  or live with it for months.

Also accepted: **no HealthKit access.** A PWA cannot read Apple Health. This is fine — Garmin is
the source of truth anyway (ADR-0001).
