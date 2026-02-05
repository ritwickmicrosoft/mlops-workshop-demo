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
- `pipeline.py` - Azure ML Pipeline definition (skeleton)

Note: this demo repo currently contains the pipeline definition only (no `trigger_function/` or `components/` folders).
