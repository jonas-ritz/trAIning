// A Log Analytics workspace is where the Container Apps Environment (see
// container-apps-environment.bicep) sends every container's stdout/stderr and platform metrics —
// `docker logs`-equivalent visibility for whatever runs in that environment.

@description('Name of the Log Analytics workspace. Unique within the resource group, not globally.')
param name string

@description('Azure region for the workspace.')
param location string

@description('How long logs are retained. 30 days is the free-tier default; longer retention is billed per GB.')
param retentionInDays int = 30

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
  }
}

output id string = logAnalytics.id

// The Container Apps Environment needs these two values to send logs here. The shared key is a
// credential (equivalent to a password for writing to this workspace), so it's marked @secure()
// on the way out — Azure then omits it from the plaintext deployment-history/outputs view in the
// portal, rather than leaving it sitting in cleartext for anyone who can read deployment history.
output customerId string = logAnalytics.properties.customerId

@secure()
output primarySharedKey string = logAnalytics.listKeys().primarySharedKey
