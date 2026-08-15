# Deploy

How the Azure infrastructure gets created and updated. For now this is a manual, one-time
bootstrap (Bicep from your own machine); a GitHub Actions workflow will later automate the
update path, but the first-time setup below stays manual either way.

## What's in `infra/` today, and what isn't

`infra/main.bicep` currently defines the **shared hosting foundation** only:

- A Log Analytics workspace (`log-training`) — where every container's logs end up.
- A Container Apps Environment (`cae-training`) — the shared host that Container Apps and
  Container App Jobs run inside. Nothing runs inside it yet.

**Not here yet, deliberately:** the Container App itself (comes with the first real deploy), and
Azure SQL / Blob Storage / Key Vault (nothing in the codebase reads or writes to them yet —
provisioning them earlier than the code that needs them just adds cost and drift risk for no
benefit). See spec.md §12 for the phase they're each introduced in.

## Prerequisites

1. **Azure CLI**, logged in: `az login` (or `az login --use-device-code` if the normal browser
   flow doesn't work in your environment — it prints a URL and a short code to enter there).
   Confirm you're on the right account/subscription afterwards: `az account show`.
2. **A pay-as-you-go subscription isn't required yet** — everything deployed so far runs on
   free-tier resources regardless of subscription type. See
   [azure-subscription.md](azure-subscription.md) for when that changes (once Foundry is in use).
3. **The resource group must already exist.** Bicep here is scoped to an existing resource group
   on purpose (see `main.bicep`'s top comment) — creating it is a separate, explicit step:
   ```bash
   az group create --name rg-training --location <region>
   ```
   Pick a region Container Apps and (later) Foundry both support. **Not every region accepts new
   resources on every subscription** — newer or free-tier subscriptions can get rejected in
   high-demand regions with `RequestDisallowedByAzure ... currently not accepting new customers`.
   If that happens, `az deployment group what-if` (below) with a different `location` override is
   a fast way to check which regions your subscription actually has access to before committing.

## Deploy

```bash
az deployment group create -g rg-training -f infra/main.bicep
```

Bicep resources default their region to the resource group's own region
(`resourceGroup().location` in `main.bicep`), so as long as the resource group is where you want
things, no extra flags are needed.

**Preview first, if you want to see the diff before it applies:**

```bash
az deployment group what-if -g rg-training -f infra/main.bicep
```

`what-if` shows exactly what would be created/changed/deleted without touching anything. Secret
outputs (see below) show as `*******` even here, not just in the final result.

## Verify

```bash
az resource list -g rg-training -o table
```

Should show `log-training` (`Microsoft.OperationalInsights/workspaces`) and `cae-training`
(`Microsoft.App/managedEnvironments`), both `Succeeded`. Same information the Azure Portal shows
under the resource group's Overview page, if you'd rather look there.

## A note on secrets in this template

The Log Analytics workspace exposes an access key (`listKeys().primarySharedKey`) that the
Container Apps Environment needs, to authenticate its log writes. That value is marked
`@secure()` on both the output that produces it and the parameter that receives it — Azure then
omits it from the plaintext deployment-history/outputs view, rather than leaving a credential
sitting in cleartext for anyone who can read deployment history. No secret in this template comes
from Key Vault (there isn't one yet) or from a `.env`/config file — it's generated and consumed
entirely within the deployment itself.
