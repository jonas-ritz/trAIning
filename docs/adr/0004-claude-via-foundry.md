# ADR-0004: Claude via Microsoft Foundry, not the Anthropic API

**Status:** Accepted
**Date:** 2026-07

## Context

The application needs programmatic LLM access. Three routes exist.

An important clarification, because it is a common misconception: **a Claude Pro subscription
cannot be used.** Pro covers the consumer chat interface and includes no API access. There is no
mechanism to route application traffic through it. Programmatic access is always per-token.

## Options considered

- **Anthropic API directly.** Simplest. An API key in Key Vault, HTTPS calls out. But it makes the
  LLM the one component living outside Azure, with its own billing, its own credential, and its own
  governance story.
- **Claude in Microsoft Foundry.** Claude is generally available in Foundry, hosted on Azure, with
  a C# SDK and Microsoft Entra authentication. Billing lands on the Azure invoice.

## Decision

Claude via Microsoft Foundry.

The deciding factor is not cost — the two are comparable — but the learning objective. Entra
authentication, Managed Identity, and Azure governance are precisely the skills this project exists
to build. Foundry means **no API keys anywhere in the system**, which is also the better security
posture.

## Consequences

- Requires an Azure subscription with a real payment method. Student, trial, and credit-only
  subscriptions do not work with Foundry.
- Requires a supported region for the deployment.
- Auth via Entra ID / Managed Identity — consistent with SQL and Blob access. One identity model
  across the whole system.
- **Prompt caching is the primary cost lever.** The system prompt, athlete profile, and goal set are
  stable across turns and must be cached.
- Model split: Haiku for per-session interpretation (high volume, bounded task), a stronger model
  for planning (low volume, high stakes).
