"""Register Feature Store entity + feature set (Azure-only workshop).

Prereqs:
- Deploy the Feature Store workspace (see infra/feature_store.bicep)
- Set env vars:
  - AZURE_SUBSCRIPTION_ID
  - AZURE_RESOURCE_GROUP (default: rg-dnd-mlops-demo)
  - AZURE_FEATURE_STORE_WORKSPACE (default: fs-dndmlops-dev)

This script registers:
- Feature Store Entity: assets/document_entity.yaml
- Feature Set: assets/document_features.yaml (spec in assets/document_features_spec.yaml)

Run (PowerShell):
  $env:AZURE_SUBSCRIPTION_ID = "..."
  $env:AZURE_RESOURCE_GROUP = "rg-dnd-mlops-demo"
  $env:AZURE_FEATURE_STORE_WORKSPACE = "fs-dndmlops-dev"
  python .\04-feature-store\register_feature_assets.py
"""

from __future__ import annotations

import os
from pathlib import Path

from azure.ai.ml import MLClient, load_feature_set, load_feature_store_entity
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential


def _get_credential():
    try:
        cred = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        cred.get_token("https://management.azure.com/.default")
        return cred
    except Exception:
        return InteractiveBrowserCredential()


def _create_or_update(ops, asset):
    if hasattr(ops, "create_or_update"):
        return ops.create_or_update(asset)
    if hasattr(ops, "begin_create_or_update"):
        poller = ops.begin_create_or_update(asset)
        return poller.result()
    raise AttributeError(f"Unsupported operations object: {type(ops).__name__}")


def main() -> None:
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "").strip()
    resource_group = os.getenv("AZURE_RESOURCE_GROUP", "rg-dnd-mlops-demo").strip()
    feature_store_ws = os.getenv("AZURE_FEATURE_STORE_WORKSPACE", "fs-dndmlops-dev").strip()

    if not subscription_id:
        raise ValueError("Missing AZURE_SUBSCRIPTION_ID")

    repo_root = Path(__file__).resolve().parents[1]
    assets_dir = Path(__file__).resolve().parent / "assets"

    entity_yml = assets_dir / "document_entity.yaml"
    feature_set_yml = assets_dir / "document_features.yaml"

    cred = _get_credential()
    ml_client = MLClient(
        credential=cred,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=feature_store_ws,
    )

    # Load + register entity
    entity = load_feature_store_entity(entity_yml)
    created_entity = _create_or_update(ml_client.feature_store_entities, entity)
    print("Registered entity:", created_entity.name, created_entity.version)

    # Load + register feature set
    feature_set = load_feature_set(feature_set_yml)

    # Secure-workspace compatibility: avoid SDK uploading local folders via SAS (shared key),
    # which is blocked when storage disables key-based auth. Setting an azureml:// URI here
    # makes the SDK skip local uploads.
    feature_set.path = f"azureml://datastores/workspaceblobstore/paths/feature_sets/{feature_set.name}/{feature_set.version}/"

    created_fs = _create_or_update(ml_client.feature_sets, feature_set)
    print("Registered feature set:", created_fs.name, created_fs.version)

    studio_url = (
        f"https://ml.azure.com/featurestores?wsid=/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{feature_store_ws}"
    )
    print("Open Feature Store workspace in Studio:")
    print(studio_url)


if __name__ == "__main__":
    main()
