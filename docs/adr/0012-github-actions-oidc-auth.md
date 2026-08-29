# ADR-0012: GitHub Actions authenticates to Azure via OIDC, not a stored secret

**Status:** Accepted
**Date:** 2026-08

## Context

The CD workflow needs to run `az deployment group create` against the subscription on every
push to `main` — it has to authenticate to Azure as *something*. The two ways GitHub Actions can
authenticate to an external cloud are a long-lived credential stored as a repo secret, or a
short-lived token minted per run via OpenID Connect (OIDC) federation.

## Options considered

- **A service principal with a client secret**, stored as a GitHub Actions secret
  (`AZURE_CLIENT_SECRET`). Simple to set up, well-documented, works everywhere. But it's a
  standing credential: it sits in GitHub's secret store indefinitely, has to be manually rotated
  before it expires (client secrets max out at 24 months) or it silently breaks CD, and if it
  ever leaks, it's valid from anywhere until someone notices and revokes it.
- **OIDC federated credential.** Entra ID trusts GitHub's own OIDC issuer to vouch for "this
  workflow run, from this exact repo and branch, is who it claims to be," and issues a token
  valid only for the few minutes that run lasts. Nothing is stored in GitHub at all — not even a
  short-lived value — because the token is requested fresh, in-run, using GitHub's own OIDC
  provider. More moving parts to set up once (an app registration, a federated credential, an
  RBAC role assignment), and it only works from CI systems that support OIDC token requests
  (GitHub Actions does).

## Decision

OIDC federated credential. The one-time setup cost is paid once; the security property (no
credential ever at rest, nothing to rotate, nothing that can leak from GitHub's side because
there's nothing stored there to steal) holds for the life of the project.

The federated credential's trust condition is scoped to `repo:jonas-ritz/trAIning:ref:refs/heads/main`
— only workflow runs triggered from a push to `main` in this exact repo can obtain a token. A
workflow run on a fork, a different branch, or a different repo entirely gets no token, full stop.

The resulting service principal is granted a role scoped to `rg-training` only (see
docs/setup/deploy.md for which one and why), not the subscription — it can manage what's in this
resource group and nothing else.

## Consequences

- Setup requires an Entra app registration + service principal + federated credential + RBAC role
  assignment, done once via Azure CLI, documented in docs/setup/deploy.md so it's reproducible
  (e.g. after an accidental deletion) without re-deriving the steps from scratch.
- The workflow needs `permissions: id-token: write` to request the OIDC token at all — easy to
  forget, since without it the login step fails with an unhelpful error rather than an obvious
  "missing permission" one.
- Three non-secret identifiers (client ID, tenant ID, subscription ID) are stored as GitHub
  Actions **variables**, not secrets — they identify the app registration but authenticate
  nothing by themselves, so they don't need secret-level handling.
- If this repository is ever renamed or moved to a different owner, the federated credential's
  subject condition stops matching and CD breaks — a deliberate consequence of scoping it that
  tightly, not an oversight; the fix is updating the federated credential's subject, not loosening it.
