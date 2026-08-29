# Runbook

Operational recovery steps. The collector is an unofficial dependency and *will* break eventually
(ADR-0001); when it does, write down here how you brought it back.

## CI/CD deploy failed

Check the failed run at **github.com/jonas-ritz/trAIning/actions** first — which job, which step,
failed tells you which of these it is:

- **`docker/build-push-action` step fails with `denied: permission_denied: write_package`** — the
  GHCR package's Actions access doesn't grant this repo write. Fix: the package's own settings
  page (github.com/jonas-ritz?tab=packages → `training-web` → Package settings → Manage Actions
  access) → the repo must be listed with role **Write**, not Read. This happened twice while
  setting CD up: once because no grant existed at all (the package was originally created by a
  manual `docker push` with a personal token, never linked to any repo), once because the grant
  existed but was set to Read.
- **`azure/login` step fails** — almost always the OIDC federated credential's `subject` no longer
  matches. It's scoped to `repo:jonas-ritz/trAIning:ref:refs/heads/main` exactly (ADR-0012); a
  renamed repo, renamed default branch, or a run from any other branch breaks this silently, with
  an authentication error that doesn't say why. Check `az ad app federated-credential list --id
  <appId>` matches the repo/branch that's actually running. Also check the three
  `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_SUBSCRIPTION_ID` repository variables are still set
  (Settings → Secrets and variables → Actions → Variables) — deleting/recreating the app
  registration changes the client ID and silently breaks login until these are updated.
- **`az containerapp update` step fails with an authorization error** — the service principal's
  role assignment on `rg-training` (Container Apps Contributor) may have been removed or never
  completed. See github-actions-oidc.md for how to recreate it — including the `az rest`
  workaround, since `az role assignment create` failed outright in this environment even for an
  Owner (see that doc for why).

Planned entries:
- **Collector fails to log in** — Garmin changed the internal API, or credentials/session expired.
- **No new activities for N days** — is it the collector, the upload, or the ingest function?
- **Interpretation cost spiked** — check the idempotency guard and `AgentRun` logs (see cost.md).
- **Agent replanning loop** — how to detect and stop it.
- **Restoring after a trial subscription lapsed** — see azure-subscription.md.
