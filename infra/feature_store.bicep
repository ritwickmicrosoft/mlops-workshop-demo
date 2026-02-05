// Deploy an Azure ML Feature Store workspace into the same RG as infra/main.bicep.
//
// Usage:
//   az deployment group create --resource-group <rg> --template-file infra/feature_store.bicep
//
// Notes:
// - This template assumes infra/main.bicep has already been deployed in the same RG.
// - It reuses the existing Storage Account, Key Vault, App Insights, and ACR created by main.bicep.

targetScope = 'resourceGroup'

@description('The Azure region for resources')
param location string = resourceGroup().location

@description('Base name for all resources (must match infra/main.bicep)')
param baseName string = 'dndmlops'

@description('Environment name (must match infra/main.bicep)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Feature Store workspace name')
param featureStoreWorkspaceName string = 'fs-${baseName}-${environment}'

@description('Tags to apply to all resources')
param tags object = {
  Project: 'DND-MLOps-Demo'
  Environment: environment
  Owner: 'AI-Centre'
}

var uniqueSuffix = uniqueString(resourceGroup().id)
var baseNameClean = toLower(replace(replace(baseName, '-', ''), '_', ''))
var storageAccountName = take('st${baseNameClean}${uniqueSuffix}', 24)
var keyVaultName = take('kv${baseNameClean}${uniqueSuffix}', 24)
var appInsightsName = 'appi-${baseName}-${environment}'
var containerRegistryName = 'cr${baseNameClean}${uniqueSuffix}'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource featureStoreWorkspace 'Microsoft.MachineLearningServices/workspaces@2023-10-01' = {
  name: featureStoreWorkspaceName
  location: location
  tags: tags
  kind: 'FeatureStore'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'DND MLOps Demo Feature Store'
    description: 'Azure ML Feature Store workspace for the workshop'
    featureStoreSettings: {
    }
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    containerRegistry: containerRegistry.id
    publicNetworkAccess: 'Enabled'
  }
}

output featureStoreWorkspaceName string = featureStoreWorkspace.name
output featureStoreWorkspaceId string = featureStoreWorkspace.id
