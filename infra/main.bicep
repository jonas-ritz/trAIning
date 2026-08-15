// Short explanation on what bicep is and why we use it, for the uninitiated reader:
// Bicep is a domain-specific language (DSL) for deploying Azure resources declaratively (likewise to Terraform but specifically for Azure).
// It is infrastructure as code and intended to be a more concise and readable alternative to ARM templates. Bicep files are transpiled into ARM JSON templates before deployment.
// IAC has the advantage of reproducibility, version control, and automation.
//
// Can be deployed with (might take some time to finish, depending on the region and subscription):
//   az deployment group create -g <rg> -f infra/main.bicep
//
// Entry point for bicep cascading down into the modules directory. 
@description('Azure region for every resource this template creates.')
param location string = resourceGroup().location

@description('Base name used to derive individual resource names.')
param baseName string = 'training'

@description('Full image reference for the Container App, e.g. ghcr.io/jonas-ritz/training-web:<tag>.')
param webImage string

// Log Analytics workspace: where every container's logs end up.
module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  params: {
    name: 'log-${baseName}'
    location: location
  }
}

// Container Apps Environment: the shared host that Container Apps and Container App Jobs run
// inside.
module containerAppsEnvironment 'modules/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  params: {
    name: 'cae-${baseName}'
    location: location
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsSharedKey: logAnalytics.outputs.primarySharedKey
  }
}

// The Container App: TrAIning.Web itself, running inside the environment above.
module containerApp 'modules/container-app.bicep' = {
  name: 'container-app'
  params: {
    name: 'ca-${baseName}-web'
    location: location
    containerAppsEnvironmentId: containerAppsEnvironment.outputs.id
    image: webImage
  }
}

output containerAppsEnvironmentId string = containerAppsEnvironment.outputs.id
output containerAppsEnvironmentDefaultDomain string = containerAppsEnvironment.outputs.defaultDomain
output webFqdn string = containerApp.outputs.fqdn
