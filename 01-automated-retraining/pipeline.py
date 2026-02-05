"""Azure ML Pipeline for Automated Retraining.

Demonstrates: data-driven retraining with an Azure ML pipeline and MLflow tracking.
"""

import os
from pathlib import Path

from azure.ai.ml import Input, MLClient, Output, command, dsl
from azure.identity import DefaultAzureCredential

# =============================================================================
# CONFIGURATION
# =============================================================================

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "rg-dnd-mlops-demo")
WORKSPACE_NAME = os.getenv("AZURE_ML_WORKSPACE", "mlw-dndmlops-dev")

THIS_DIR = Path(__file__).resolve().parent
COMPONENTS_DIR = THIS_DIR / "components"

# Initialize ML Client
if not SUBSCRIPTION_ID:
    raise ValueError(
        "Missing AZURE_SUBSCRIPTION_ID. Set it as an environment variable before running this script."
    )

credential = DefaultAzureCredential()
ml_client = MLClient(credential, SUBSCRIPTION_ID, RESOURCE_GROUP, WORKSPACE_NAME)

# =============================================================================
# PIPELINE COMPONENTS
# =============================================================================

# Use sklearn-1.5 curated environment (has numpy<2.0, sklearn 1.5+)
PIPELINE_ENV = "azureml://registries/azureml/environments/sklearn-1.5/labels/latest"

# Data Preparation Component
data_prep_component = command(
    name="data_preparation",
    display_name="Prepare Training Data",
    description="Fetch and preprocess data for training (OpenML Spambase)",
    inputs={
        "noise_std": Input(type="number", default=0.0),
    },
    outputs={
        "prepared_data": Output(type="uri_folder"),
    },
    code=str(COMPONENTS_DIR / "data_prep"),
    command="python prep.py --output ${{outputs.prepared_data}} --noise_std ${{inputs.noise_std}}",
    environment=PIPELINE_ENV,
)

# Training Component
train_component = command(
    name="train_model",
    display_name="Train Model",
    description="Train ML model with MLflow tracking",
    inputs={
        "training_data": Input(type="uri_folder"),
        "n_estimators": Input(type="integer", default=100),
        "max_depth": Input(type="integer", default=12),
    },
    outputs={
        "model": Output(type="mlflow_model"),
        "metrics": Output(type="uri_file"),
    },
    code=str(COMPONENTS_DIR / "train"),
    command="""python train.py \
        --data ${{inputs.training_data}} \
        --n_estimators ${{inputs.n_estimators}} \
        --max_depth ${{inputs.max_depth}} \
        --model_output ${{outputs.model}} \
        --metrics_output ${{outputs.metrics}}""",
    environment=PIPELINE_ENV,
)

# Evaluation Component
evaluate_component = command(
    name="evaluate_model",
    display_name="Evaluate Model",
    description="Compare new model against production model",
    inputs={
        "model": Input(type="mlflow_model"),
        "test_data": Input(type="uri_folder"),
        "min_accuracy": Input(type="number", default=0.90),
    },
    outputs={
        "evaluation_report": Output(type="uri_file"),
        "deploy_flag": Output(type="uri_file"),
    },
    code=str(COMPONENTS_DIR / "evaluate"),
    command="""python evaluate.py \
        --model ${{inputs.model}} \
        --test_data ${{inputs.test_data}} \
        --min_accuracy ${{inputs.min_accuracy}} \
        --report_output ${{outputs.evaluation_report}} \
        --deploy_flag ${{outputs.deploy_flag}}""",
    environment=PIPELINE_ENV,
)

# Registration Component
register_component = command(
    name="register_model",
    display_name="Register Model",
    description="Register model if it passes evaluation",
    inputs={
        "model": Input(type="mlflow_model"),
        "deploy_flag": Input(type="uri_file"),
        "model_name": Input(type="string"),
    },
    code=str(COMPONENTS_DIR / "register"),
    command="""python register.py \
        --model ${{inputs.model}} \
        --deploy_flag ${{inputs.deploy_flag}} \
        --model_name ${{inputs.model_name}}""",
    environment=PIPELINE_ENV,
)


# =============================================================================
# PIPELINE DEFINITION
# =============================================================================

@dsl.pipeline(
    name="automated-retraining-pipeline",
    description="End-to-end retraining pipeline with model comparison",
    compute="cpu-cluster",
)
def retraining_pipeline(
    n_estimators: int = 100,
    max_depth: int = 12,
    min_accuracy: float = 0.90,
    noise_std: float = 0.0,
    model_name: str = "classification-model",
):
    """
    Automated Retraining Pipeline
    
    Steps:
    1. Data Preparation - Clean and split data
    2. Training - Train new model with MLflow tracking
    3. Evaluation - Compare against production model
    4. Registration - Register if performance improves
    """
    
    # Step 1: Prepare data (fetches OpenML inside the job)
    prep_step = data_prep_component(noise_std=noise_std)
    
    # Step 2: Train model
    train_step = train_component(
        training_data=prep_step.outputs.prepared_data,
        n_estimators=n_estimators,
        max_depth=max_depth,
    )
    
    # Step 3: Evaluate model
    eval_step = evaluate_component(
        model=train_step.outputs.model,
        test_data=prep_step.outputs.prepared_data,
        min_accuracy=min_accuracy,
    )
    
    # Step 4: Register if approved
    register_step = register_component(
        model=train_step.outputs.model,
        deploy_flag=eval_step.outputs.deploy_flag,
        model_name=model_name,
    )
    
    return {
        "model": train_step.outputs.model,
        "metrics": train_step.outputs.metrics,
        "evaluation_report": eval_step.outputs.evaluation_report,
    }


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Create pipeline instance
    pipeline_job = retraining_pipeline(
        n_estimators=100,
        max_depth=12,
        min_accuracy=0.90,
        noise_std=0.0,
        model_name="dnd-classification-model",
    )
    
    # Submit pipeline
    pipeline_job = ml_client.jobs.create_or_update(
        pipeline_job,
        experiment_name="automated-retraining",
    )
    
    print(f"Pipeline submitted: {pipeline_job.name}")
    print(f"Studio URL: {pipeline_job.studio_url}")
