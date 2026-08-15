// The Container Apps Environment is the shared host: a boundary that groups every Container App
// and Container App Job that runs in it (spec.md §4). Wired to send logs to the Log Analytics
// workspace from log-analytics.bicep.

@description('Name of the Container Apps Environment. Unique within the resource group, not globally.')
param name string

@description('Azure region.')
param location string

@description('Log Analytics workspace ID (customerId) to send container logs to.')
param logAnalyticsCustomerId string

@description('Log Analytics workspace primary shared key, used to authenticate log writes.')
@secure()
param logAnalyticsSharedKey string

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
  }
}

output id string = containerAppsEnvironment.id
output name string = containerAppsEnvironment.name

// The domain every Container App in this environment gets a subdomain of, e.g.
// <app-name>.<defaultDomain> — this is what the app's public URL is built from once a
// Container App is deployed into this environment.
output defaultDomain string = containerAppsEnvironment.properties.defaultDomain
