# Feature Store

This module demonstrates how to share and reuse features across the organization using Azure ML Managed Feature Store.

## Why Feature Store?

| Challenge | Solution |
|-----------|----------|
| Feature duplication across teams | Centralized feature repository |
| Training/serving skew | Same feature logic for both |
| Feature discovery | Searchable feature catalog |
| Point-in-time correctness | Time-travel for historical features |
| Real-time serving | Materialized features for low latency |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Azure ML Feature Store                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐        ┌──────────────────────────────────┐   │
│  │  Raw Data       │        │       Feature Sets                │   │
│  │  Sources        │        │  ┌────────────────────────────┐  │   │
│  │  ┌───────────┐  │        │  │ customer_features          │  │   │
│  │  │ Azure SQL │──┼───────►│  │ - customer_id              │  │   │
│  │  └───────────┘  │        │  │ - total_purchases          │  │   │
│  │  ┌───────────┐  │        │  │ - avg_order_value          │  │   │
│  │  │ Blob      │──┼───────►│  │ - days_since_last_order    │  │   │
│  │  │ Storage   │  │        │  └────────────────────────────┘  │   │
│  │  └───────────┘  │        │  ┌────────────────────────────┐  │   │
│  │  ┌───────────┐  │        │  │ document_features          │  │   │
│  │  │ Event Hub │──┼───────►│  │ - doc_id                   │  │   │
│  │  └───────────┘  │        │  │ - word_count               │  │   │
│  └─────────────────┘        │  │ - pii_score                │  │   │
│                              │  │ - classification_embedding │  │   │
│                              │  └────────────────────────────┘  │   │
│                              └──────────────────────────────────┘   │
│                                           │                          │
│                    ┌──────────────────────┼──────────────────────┐  │
│                    ▼                      ▼                      ▼  │
│            ┌─────────────┐        ┌─────────────┐        ┌─────────┐
│            │  Training   │        │   Batch     │        │  Online │
│            │  Jobs       │        │  Inference  │        │  Serving│
│            └─────────────┘        └─────────────┘        └─────────┘
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Feature Store vs. Traditional Approach

### Traditional (Problems)
```python
# Team A's approach
def get_customer_features_team_a(customer_id):
    # Custom logic, different from Team B
    return {"avg_spend": calculate_avg_v1(customer_id)}

# Team B's approach  
def get_customer_features_team_b(customer_id):
    # Different logic, causes inconsistency
    return {"avg_spend": calculate_avg_v2(customer_id)}
```

### Feature Store (Solution)
```python
# Single source of truth
from azure.ai.ml.entities import FeatureStoreClient

fs_client = FeatureStoreClient(...)
features = fs_client.get_online_features(
    feature_set="customer_features:1",
    entity_keys={"customer_id": "12345"}
)
```

## Azure ML Feature Store Components

| Component | Description |
|-----------|-------------|
| **Feature Store** | Top-level container for features |
| **Feature Set** | Logical grouping of related features |
| **Feature** | Individual feature with transformation logic |
| **Entity** | Business object (customer, product, document) |
| **Materialization** | Precomputed features for performance |

## Hands-On Exercises

1. **Exercise 1**: Create a feature store workspace
2. **Exercise 2**: Define and register feature sets
3. **Exercise 3**: Materialize features for training
4. **Exercise 4**: Serve features in real-time

## Azure-only Workshop Quickstart

### 1) Deploy the Feature Store workspace

This repo provisions the Feature Store as a separate Azure ML workspace of kind `FeatureStore`.

Prereq: deploy [infra/main.bicep](../infra/main.bicep) first (creates Storage, Key Vault, App Insights, ACR).

Then deploy:

```bash
az deployment group create \
    --resource-group rg-dnd-mlops-demo \
    --template-file infra/feature_store.bicep \
    --parameters baseName=<same-baseName-as-main.bicep> environment=dev
```

By default the Feature Store workspace name is `fs-dndmlops-dev`.

### 2) Register an entity + feature set

Set environment variables:

```powershell
$env:AZURE_SUBSCRIPTION_ID = "<subscription-id>"
$env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
$env:AZURE_FEATURE_STORE_WORKSPACE = "fs-dndmlops-dev"
```

Run:

```powershell
python .\04-feature-store\register_feature_assets.py
```

This registers:
- Entity: [04-feature-store/assets/document_entity.yaml](assets/document_entity.yaml)
- Feature set + spec: [04-feature-store/assets/document_features.yaml](assets/document_features.yaml)

### 3) Demo in Azure ML Studio

Open the Feature Store workspace and show:
- Entities (the `document` entity)
- Feature sets (the `document_features` set)
