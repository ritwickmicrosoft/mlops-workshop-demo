"""
Azure ML Managed Feature Store Setup
Demonstrates: Feature definition, materialization, and serving
"""

from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    FeatureStore,
    FeatureSet,
    FeatureSetSpec,
    FeatureEntity,
    FeatureStoreEntity,
    MaterializationSettings,
    MaterializationComputeResource,
    RecurrenceTrigger,
)
from azure.identity import DefaultAzureCredential
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-dnd-mlops-demo")
FEATURE_STORE_NAME = os.getenv("FEATURE_STORE_NAME", "fs-dnd-mlops-demo")

credential = DefaultAzureCredential()


# =============================================================================
# FEATURE STORE SETUP
# =============================================================================

def create_feature_store():
    """
    Create an Azure ML Managed Feature Store.
    """
    
    # Use ARM client for feature store creation
    from azure.mgmt.machinelearningservices import MachineLearningServicesMgmtClient
    
    ml_mgmt_client = MachineLearningServicesMgmtClient(credential, SUBSCRIPTION_ID)
    
    feature_store = {
        "location": "eastus",
        "sku": {"name": "Basic"},
        "kind": "FeatureStore",
        "properties": {
            "description": "DND MLOps Demo Feature Store",
            "friendlyName": "DND Feature Store",
        },
    }
    
    result = ml_mgmt_client.workspaces.begin_create_or_update(
        RESOURCE_GROUP,
        FEATURE_STORE_NAME,
        feature_store
    ).result()
    
    print(f"Feature Store created: {result.name}")
    return result


# =============================================================================
# FEATURE ENTITY DEFINITION
# =============================================================================

def create_document_entity():
    """
    Create an entity representing a document for classification.
    """
    
    document_entity_yaml = """
$schema: http://azureml/sdk-2-0/FeatureStoreEntity.json
name: document
version: "1"
description: A document entity for classification features
index_columns:
  - name: document_id
    type: string
"""
    
    # Save to file for registration
    entity_path = "./feature_store/entities/document.yaml"
    os.makedirs(os.path.dirname(entity_path), exist_ok=True)
    with open(entity_path, "w") as f:
        f.write(document_entity_yaml)
    
    return entity_path


# =============================================================================
# FEATURE SET DEFINITION
# =============================================================================

def create_document_features():
    """
    Create a feature set for document classification.
    
    These features can be shared across multiple models:
    - Document Classification
    - PII Detection
    - Security Marking
    """
    
    feature_set_yaml = """
$schema: http://azureml/sdk-2-0/FeatureSetSpec.json
source:
  type: parquet
  path: azureml://datastores/workspaceblobstore/paths/features/document_features/
  timestamp_column:
    name: event_timestamp
entity:
  - name: document
    version: "1"
    keys:
      - document_id
features:
  - name: word_count
    type: integer
    description: Total word count in document
    
  - name: char_count
    type: integer
    description: Total character count in document
    
  - name: page_count
    type: integer
    description: Number of pages in document
    
  - name: has_tables
    type: boolean
    description: Whether document contains tables
    
  - name: has_images
    type: boolean
    description: Whether document contains images
    
  - name: pii_score
    type: float
    description: PII detection confidence score (0-1)
    
  - name: language_detected
    type: string
    description: Detected primary language
    
  - name: text_embedding
    type: array
    description: Document text embedding vector (1536 dimensions)
    
  - name: classification_confidence
    type: float
    description: Previous classification confidence score
    
  - name: days_since_creation
    type: integer
    description: Days since document was created
"""
    
    feature_set_path = "./feature_store/featuresets/document_features.yaml"
    os.makedirs(os.path.dirname(feature_set_path), exist_ok=True)
    with open(feature_set_path, "w") as f:
        f.write(feature_set_yaml)
    
    return feature_set_path


# =============================================================================
# FEATURE TRANSFORMATION CODE
# =============================================================================

FEATURE_TRANSFORMATION_CODE = '''
"""
Feature transformation code for document features.
This code runs during materialization to compute features from raw data.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType


def compute_document_features(raw_documents: DataFrame) -> DataFrame:
    """
    Transform raw document data into features.
    
    Input columns:
    - document_id: string
    - content: string (extracted text)
    - created_date: timestamp
    - file_type: string
    
    Output: DataFrame with computed features
    """
    
    features = raw_documents.select(
        F.col("document_id"),
        F.current_timestamp().alias("event_timestamp"),
        
        # Text statistics
        F.size(F.split(F.col("content"), " ")).alias("word_count"),
        F.length(F.col("content")).alias("char_count"),
        
        # Document structure (simplified)
        F.when(F.col("file_type") == "pdf", 
               F.ceil(F.length(F.col("content")) / 3000)).otherwise(1).alias("page_count"),
        
        F.col("content").contains("<table").alias("has_tables"),
        F.col("content").contains("<img").alias("has_images"),
        
        # Language detection (placeholder - would use Azure AI Language)
        F.lit("en").alias("language_detected"),
        
        # Days since creation
        F.datediff(F.current_date(), F.col("created_date")).alias("days_since_creation"),
    )
    
    return features
'''


# =============================================================================
# MATERIALIZATION SETUP
# =============================================================================

def configure_materialization():
    """
    Configure feature materialization for offline and online stores.
    """
    
    materialization_config = {
        "offline_store": {
            "type": "azure_blob",
            "path": "azureml://datastores/workspaceblobstore/paths/feature_store/offline/",
        },
        "online_store": {
            "type": "redis",  # Requires Azure Cache for Redis
            "connection_string": "${REDIS_CONNECTION_STRING}",
        },
        "schedule": {
            "frequency": "daily",
            "time": "02:00",  # Run at 2 AM
        },
        "compute": {
            "instance_type": "Standard_E4s_v3",
            "spark_version": "3.3",
        },
    }
    
    return materialization_config


# =============================================================================
# FEATURE RETRIEVAL FOR TRAINING
# =============================================================================

def get_training_features(
    feature_store_uri: str,
    training_data_path: str,
    feature_set_name: str = "document_features",
    feature_set_version: str = "1",
):
    """
    Retrieve features for model training with point-in-time correctness.
    
    This ensures training uses features as they existed at the time
    of each training example, preventing data leakage.
    """
    
    from azureml.featurestore import FeatureStoreClient
    from azureml.featurestore.offline_retrieval import get_offline_features
    
    # Initialize feature store client
    fs_client = FeatureStoreClient(
        credential=credential,
        subscription_id=SUBSCRIPTION_ID,
        resource_group=RESOURCE_GROUP,
        name=FEATURE_STORE_NAME,
    )
    
    # Load training entities (documents with labels)
    training_entities = spark.read.parquet(training_data_path)
    
    # Get features with point-in-time join
    training_features = get_offline_features(
        feature_store=fs_client,
        observation_data=training_entities,
        feature_sets=[
            {
                "name": feature_set_name,
                "version": feature_set_version,
                "features": [
                    "word_count",
                    "char_count",
                    "page_count",
                    "has_tables",
                    "pii_score",
                    "text_embedding",
                ],
            }
        ],
        entity_columns=["document_id"],
        timestamp_column="event_timestamp",
    )
    
    return training_features


# =============================================================================
# ONLINE FEATURE RETRIEVAL FOR INFERENCE
# =============================================================================

def get_inference_features(document_ids: list):
    """
    Retrieve features in real-time for model inference.
    
    Uses materialized online store for low-latency serving.
    """
    
    from azureml.featurestore import FeatureStoreClient
    
    fs_client = FeatureStoreClient(
        credential=credential,
        subscription_id=SUBSCRIPTION_ID,
        resource_group=RESOURCE_GROUP,
        name=FEATURE_STORE_NAME,
    )
    
    features = fs_client.get_online_features(
        feature_set="document_features:1",
        entity_keys=[{"document_id": doc_id} for doc_id in document_ids],
        feature_names=[
            "word_count",
            "char_count", 
            "page_count",
            "pii_score",
            "text_embedding",
        ],
    )
    
    return features.to_dict()


if __name__ == "__main__":
    print("=" * 60)
    print("Azure ML Feature Store Setup")
    print("=" * 60)
    
    # Create entity definition
    entity_path = create_document_entity()
    print(f"Entity definition created: {entity_path}")
    
    # Create feature set definition
    feature_set_path = create_document_features()
    print(f"Feature set definition created: {feature_set_path}")
    
    # Save transformation code
    transform_path = "./feature_store/code/transform.py"
    os.makedirs(os.path.dirname(transform_path), exist_ok=True)
    with open(transform_path, "w") as f:
        f.write(FEATURE_TRANSFORMATION_CODE)
    print(f"Transformation code created: {transform_path}")
    
    print("\nNext steps:")
    print("1. Deploy the feature store using Azure CLI or Portal")
    print("2. Register the entity and feature set")
    print("3. Configure and trigger materialization")
    print("4. Use features in training and inference")
