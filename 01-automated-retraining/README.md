# Automated Retraining Pipeline

This module demonstrates how to set up automated model retraining when data changes.

## Architecture

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Azure Blob      │────►│  Event Grid     │────►│  Azure Function  │
│  (new data)      │     │  (trigger)      │     │  (orchestrator)  │
└──────────────────┘     └─────────────────┘     └────────┬─────────┘
                                                          │
                                                          ▼
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Model Registry  │◄────│  Azure ML       │◄────│  Retrain         │
│  (if approved)   │     │  Pipeline       │     │  Pipeline        │
└──────────────────┘     └─────────────────┘     └──────────────────┘
```

## Triggering Options

### Option 1: Event-Driven (Data Change)
- New files uploaded to Blob Storage
- Event Grid detects the change
- Triggers Azure Function or Logic App
- Starts Azure ML Pipeline

### Option 2: Scheduled Retraining
- Azure ML Pipeline Schedule
- Runs daily/weekly/monthly
- Checks for new data before training

### Option 3: Performance-Driven
- Model monitoring detects drift
- Alert triggers retraining pipeline
- Automated or manual approval

## Hands-On Exercises

1. **Exercise 1**: Set up Event Grid trigger
2. **Exercise 2**: Create Azure ML Pipeline
3. **Exercise 3**: Implement model comparison logic
4. **Exercise 4**: Set up approval gates

## Files in This Module

| File | Purpose |
|------|---------|
| `pipeline.py` | Azure ML Pipeline definition with 4-step DAG |
| `submit_pipeline.py` | Submit the pipeline job to Azure ML |
| `simulate_event_trigger.py` | Simulate an event-driven retrain (adds noise) |
| `components/data_prep/prep.py` | Fetch & preprocess OpenML Spambase |
| `components/train/train.py` | Train RandomForest with MLflow tracking |
| `components/evaluate/evaluate.py` | Compare new model against accuracy threshold |
| `components/register/register.py` | Register model if evaluation passes |
