# Runbook

> Placeholder — fill in the first time something breaks, then keep it current.

Operational recovery steps. The collector is an unofficial dependency and *will* break eventually
(ADR-0001); when it does, write down here how you brought it back.

Planned entries:
- **Collector fails to log in** — Garmin changed the internal API, or credentials/session expired.
- **No new activities for N days** — is it the collector, the upload, or the ingest function?
- **Interpretation cost spiked** — check the idempotency guard and `AgentRun` logs (see cost.md).
- **Agent replanning loop** — how to detect and stop it.
- **Restoring after a trial subscription lapsed** (ADR-0012).
