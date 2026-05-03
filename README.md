# Automation Failure Predictor

## What is it?

Automation Failure Predictor is a FastAPI backend that receives automation execution records and predicts the risk of failure using deterministic, explainable rules.

It stores each execution in SQLite together with the generated prediction result, so the API can also return simple operational metrics.

## Why was it built?

This is a portfolio project based on production support and RPA reliability scenarios.

The goal is to show backend API design, data validation, persistence, testing, and practical analytics for automation operations without adding unnecessary complexity.

It is designed for contexts where support teams need to quickly identify executions that may require investigation before they affect users or business processes.

## How does it work?

The API receives an automation execution record with fields such as status, duration, retry count, error details, and environment.

A rule-based prediction service calculates a risk score from 0 to 100. The rules are transparent:

- Failed and timeout statuses increase risk.
- High retry counts increase risk.
- Long durations increase risk.
- Known error types increase risk.
- Production executions increase operational severity.

The response includes:

- risk_score
- risk_level
- probable_causes
- recommended_actions
- explanation

No machine learning model or external LLM call is used. The scoring is deterministic and easy to inspect.

## How do I run it?

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
python -m uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

Docker option:

```bash
docker compose up --build
```

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Basic project information |
| GET | `/health` | Health check |
| POST | `/executions` | Store an execution and its generated prediction |
| GET | `/executions` | List stored executions |
| GET | `/executions/{id}` | Retrieve one execution by ID |
| GET | `/metrics` | Return counts by status, counts by risk level, and average risk score |
| POST | `/predict` | Generate a prediction without storing the execution |

## Example payloads

Prediction request:

```json
{
  "automation_name": "invoice-processing",
  "status": "timeout",
  "duration_seconds": 1250,
  "retry_count": 3,
  "error_type": "network",
  "error_message": "Connection unavailable from provider gateway",
  "started_at": "2026-05-03T10:30:00Z",
  "environment": "production"
}
```

Example response:

```json
{
  "risk_score": 100,
  "risk_level": "critical",
  "probable_causes": [
    "Execution ended by timeout.",
    "Retry count is elevated.",
    "Execution duration is long.",
    "Error type 'network' is associated with operational risk.",
    "Error message suggests an external dependency problem.",
    "Production executions have higher operational severity."
  ],
  "recommended_actions": [
    "Review timeout thresholds, external system latency, and long-running steps.",
    "Review retry logs for unstable dependencies or flaky automation steps.",
    "Compare the duration with the normal baseline for this automation.",
    "Classify the error source and confirm whether it is automation, data, or dependency related.",
    "Check dependency health, network stability, and provider incidents.",
    "Prioritize investigation and communicate risk to support stakeholders."
  ],
  "explanation": "Risk score 100/100 calculated from status='timeout', retry_count=3, duration_seconds=1250.0, error_type='network', and environment='production'."
}
```

## Tests

Run:

```bash
python -m pytest
```

The test suite covers:

- health endpoint
- prediction endpoint
- creating executions
- listing executions
- metrics endpoint
- low, medium, high, and critical prediction scenarios

## Tech stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Pytest
- Docker

## Project status

Initial portfolio version.

The project intentionally uses deterministic rules instead of machine learning. A future version could add trend analysis, historical baselines, or an ML model after enough real execution data exists.
