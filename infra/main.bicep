// Bicep template for MLOps Demo Infrastructure
// Deploy using: az deployment group create --resource-group rg-dnd-mlops-demo --template-file main.bicep

targetScope = 'resourceGroup'

// ============================================================================
// PARAMETERS
// ============================================================================

@description('The Azure region for resources')
param location string = resourceGroup().location

@description('Base name for all resources')
param baseName string = 'dndmlops'

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Tags to apply to all resources')
param tags object = {
  Project: 'DND-MLOps-Demo'
  Environment: environment
  Owner: 'AI-Centre'
}

// ============================================================================
// VARIABLES
// ============================================================================

var uniqueSuffix = uniqueString(resourceGroup().id)
var baseNameClean = toLower(replace(replace(baseName, '-', ''), '_', ''))
var workspaceName = 'mlw-${baseName}-${environment}'
var storageAccountName = take('st${baseNameClean}${uniqueSuffix}', 24)
var keyVaultName = take('kv${baseNameClean}${uniqueSuffix}', 24)
var appInsightsName = 'appi-${baseName}-${environment}'
var containerRegistryName = 'cr${baseNameClean}${uniqueSuffix}'
var logAnalyticsName = 'log-${baseName}-${environment}'

// ============================================================================
// LOG ANALYTICS WORKSPACE
// ============================================================================

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 90
  }
}

// ============================================================================
// APPLICATION INSIGHTS
// ============================================================================

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ============================================================================
// STORAGE ACCOUNT
// ============================================================================

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// ============================================================================
// KEY VAULT
// ============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// ============================================================================
// CONTAINER REGISTRY
// ============================================================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
  }
}

// ============================================================================
// AZURE MACHINE LEARNING WORKSPACE
// ============================================================================

resource mlWorkspace 'Microsoft.MachineLearningServices/workspaces@2023-10-01' = {
  name: workspaceName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: 'DND MLOps Demo Workspace'
    description: 'Azure ML workspace for MLOps hackathon demo'
    storageAccount: storageAccount.id
    keyVault: keyVault.id
    applicationInsights: appInsights.id
    containerRegistry: containerRegistry.id
    publicNetworkAccess: 'Enabled'
  }
}

// ============================================================================
// COMPUTE CLUSTER
// ============================================================================

resource computeCluster 'Microsoft.MachineLearningServices/workspaces/computes@2023-10-01' = {
  parent: mlWorkspace
  name: 'cpu-cluster'
  location: location
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: 'Standard_DS3_v2'
      vmPriority: 'Dedicated'
      scaleSettings: {
        minNodeCount: 0
        maxNodeCount: 4
        nodeIdleTimeBeforeScaleDown: 'PT5M'
      }
    }
  }
}

// ============================================================================
// DIAGNOSTIC SETTINGS (for Audit Logging)
// ============================================================================

resource mlWorkspaceDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'mlworkspace-diagnostics'
  scope: mlWorkspace
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

output workspaceName string = mlWorkspace.name
output workspaceId string = mlWorkspace.id
output storageAccountName string = storageAccount.name
output keyVaultName string = keyVault.name
output appInsightsName string = appInsights.name
output containerRegistryName string = containerRegistry.name
output logAnalyticsId string = logAnalytics.id
