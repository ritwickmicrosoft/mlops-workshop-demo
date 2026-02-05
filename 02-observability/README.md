# Observability & Model Monitoring

This module demonstrates how to set up dashboards for model performance and data health.

## Azure ML Model Monitoring Features

### 1. Data Drift Detection
Monitors statistical changes in input features over time.

### 2. Prediction Drift
Monitors changes in model prediction distributions.

### 3. Data Quality
Monitors for null values, out-of-range values, and type mismatches.

### 4. Feature Attribution Drift
Monitors changes in feature importance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Observability Stack                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ Model       │    │ Application │    │ Azure       │             │
│  │ Endpoint    │───►│ Insights    │───►│ Monitor     │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│         │                                     │                      │
│         ▼                                     ▼                      │
│  ┌─────────────┐                      ┌─────────────┐              │
│  │ Azure ML    │                      │ Power BI /  │              │
│  │ Monitoring  │─────────────────────►│ Workbooks   │              │
│  └─────────────┘                      └─────────────┘              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Metrics to Monitor

| Category | Metrics |
|----------|---------|
| **Data Drift** | Jensen-Shannon distance, Population Stability Index |
| **Model Performance** | Accuracy, Precision, Recall, F1, AUC |
| **Operational** | Latency, Throughput, Error Rate, 5xx/4xx |
| **Data Quality** | Null rate, Out-of-range rate, Type errors |

## Alerting Strategy

| Alert Level | Condition | Action |
|-------------|-----------|--------|
| **Warning** | Drift score > 0.1 | Email notification |
| **Critical** | Drift score > 0.3 | Trigger retraining |
| **Severe** | Model accuracy < threshold | Rollback + alert |

## Hands-On Exercises

1. **Exercise 1**: Enable model monitoring
2. **Exercise 2**: Create custom metrics with App Insights
3. **Exercise 3**: Build Azure Monitor Workbook dashboard
4. **Exercise 4**: Set up alerts and action groups
