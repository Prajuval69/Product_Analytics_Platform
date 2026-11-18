# Machine Learning Specification

## Objective
Predict whether an eligible user will churn during a future prediction horizon.

## Leakage prevention
Only features available as of the observation cutoff may be used. Do not use cancellation/churn events occurring after the cutoff, future revenue, future support tickets or post-outcome activity.

## Features
Possible features:
- sessions in observation window
- active days
- event count
- feature diversity
- key-feature usage
- days since last activity
- support ticket count up to cutoff
- subscription tenure
- historical revenue up to cutoff
- plan type

## Models
- Logistic Regression baseline
- Random Forest optional

## Evaluation
Use time-aware splitting where possible. Report:
- ROC-AUC
- precision
- recall
- F1
- confusion matrix

Save:
- trained model
- feature list
- evaluation metrics
- predictions
- risk bands

Explain limitations: synthetic data, simulated relationships and no claim of real-world predictive validity.
