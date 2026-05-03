import os
from collections.abc import Generator

os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import ExecutionRecord


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database() -> None:
    db = TestingSessionLocal()
    try:
        db.query(ExecutionRecord).delete()
        db.commit()
    finally:
        db.close()


def sample_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "automation_name": "order-sync",
        "status": "failed",
        "duration_seconds": 640,
        "retry_count": 2,
        "error_type": "selector",
        "error_message": "Button selector not found",
        "environment": "production",
    }
    payload.update(overrides)
    return payload


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_prediction_endpoint_does_not_store_execution() -> None:
    response = client.post("/predict", json=sample_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] > 0
    assert body["risk_level"] in {"low", "medium", "high", "critical"}

    metrics_response = client.get("/metrics")
    assert metrics_response.json()["total_executions"] == 0


def test_create_execution_stores_prediction() -> None:
    response = client.post("/executions", json=sample_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["automation_name"] == "order-sync"
    assert body["risk_level"] in {"high", "critical"}
    assert body["probable_causes"]
    assert body["recommended_actions"]


def test_list_executions() -> None:
    client.post("/executions", json=sample_payload(automation_name="daily-report"))
    client.post("/executions", json=sample_payload(automation_name="payment-reconciliation", status="timeout"))

    response = client.get("/executions")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {item["automation_name"] for item in body} == {"daily-report", "payment-reconciliation"}


def test_get_execution_by_id() -> None:
    create_response = client.post("/executions", json=sample_payload())
    execution_id = create_response.json()["id"]

    response = client.get(f"/executions/{execution_id}")

    assert response.status_code == 200
    assert response.json()["id"] == execution_id


def test_metrics_endpoint() -> None:
    client.post("/executions", json=sample_payload(status="success", retry_count=0, error_type=None))
    client.post("/executions", json=sample_payload(status="timeout", retry_count=5))

    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["total_executions"] == 2
    assert body["counts_by_status"]["success"] == 1
    assert body["counts_by_status"]["timeout"] == 1
    assert body["average_risk_score"] > 0
