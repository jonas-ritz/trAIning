// The Container App: the actual running instance of TrAIning.Web, hosted inside the Container
// Apps Environment from container-apps-environment.bicep. Pulls a pre-built image from GHCR —
// this template never builds anything itself.

@description('Name of the Container App. Unique within the resource group, not globally.')
param name string

@description('Azure region.')
param location string

@description('Resource ID of the Container Apps Environment this app runs inside.')
param containerAppsEnvironmentId string

@description('Full image reference to run, e.g. ghcr.io/jonas-ritz/training-web:<tag>.')
param image string

@description('Port the container listens on (must match the Dockerfile\'s ASPNETCORE_HTTP_PORTS).')
param targetPort int = 8080

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      // External ingress terminates TLS here and forwards plain HTTP to the container on
      // targetPort — see docs/reference/tls-termination.md for the full request flow.
      ingress: {
        external: true
        targetPort: targetPort
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'web'
          image: image
          // Smallest resource allocation Container Apps allows on the Consumption plan —
          // appropriate for a skeleton with no load yet.
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      // minReplicas: 0 is what makes this scale-to-zero (spec.md §11's ~0€ cost line) — Azure
      // spins a replica up on the first request after idling and back down after inactivity.
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output id string = containerApp.id
