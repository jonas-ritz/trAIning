# One-time setup: letting GitHub Actions deploy to Azure

`.github/workflows/ci.yml`'s deploy job authenticates to Azure via an OIDC federated credential,
not a stored secret (ADR-0012) — nothing here is a password to remember or rotate, but the trust
relationship itself has to be created once, by hand:

```bash
# 1. An Entra app registration — the identity GitHub Actions will authenticate as.
az ad app create --display-name "trAIning-github-actions-cd"
# → note the appId this returns; it's AZURE_CLIENT_ID below

# 2. A service principal for that app — the thing Azure RBAC roles actually attach to.
az ad sp create --id <appId>
# → note the id this returns (the service principal's object ID, different from appId)

# 3. The federated credential: trusts GitHub's OIDC tokens, but only for pushes to main on this
#    exact repo. A run from a fork, a different branch, or a different repo gets no token.
az ad app federated-credential create --id <appId> --parameters '{
  "name": "github-actions-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:jonas-ritz/trAIning:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'

# 4. Grant the role the deploy job actually needs — Container Apps Contributor (read/write on
#    Container Apps, read-only on the environment, nothing else in the resource group), scoped
#    to rg-training only, not the whole subscription.
```

**Step 4 — `az role assignment create` may fail** with
`(MissingSubscription) The request did not have a subscription or a valid tenant level resource
provider`, even for an Owner, even with a perfectly valid `--scope`. This looked like a
permissions problem but wasn't — `az role assignment list --all` (no explicit scope) worked fine
and confirmed full Owner access; only commands with an explicit `--scope` failed, which pointed
at a client-side bug in this Azure CLI version rather than anything about the account or
subscription. The workaround is to call the same ARM REST API directly, bypassing the CLI's
role-assignment command wrapper entirely:

```bash
az role definition list --name "Container Apps Contributor" --query "[0].name" -o tsv
# → the role definition GUID, e.g. 358470bc-b998-42bd-ab17-a7e34c199c0f

az rest --method put \
  --url "https://management.azure.com/subscriptions/<subscription-id>/resourceGroups/rg-training/providers/Microsoft.Authorization/roleAssignments/<a-new-random-guid>?api-version=2022-04-01" \
  --body '{
    "properties": {
      "roleDefinitionId": "/subscriptions/<subscription-id>/providers/Microsoft.Authorization/roleDefinitions/<role-guid-from-above>",
      "principalId": "<service-principal-object-id-from-step-2>",
      "principalType": "ServicePrincipal"
    }
  }'
```

Finally, add three **repository variables** (not secrets — none of these authenticate anything by
themselves, they only identify the app registration): **github.com/jonas-ritz/trAIning → Settings
→ Secrets and variables → Actions → Variables tab → New repository variable**:

| Variable | Value |
|---|---|
| `AZURE_CLIENT_ID` | the `appId` from step 1 |
| `AZURE_TENANT_ID` | your Entra tenant ID (`az account show --query tenantId`) |
| `AZURE_SUBSCRIPTION_ID` | the subscription ID (`az account show --query id`) |
