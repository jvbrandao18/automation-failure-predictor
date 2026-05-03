from app.prediction_service import predict_failure_risk
from app.schemas import ExecutionCreate


def make_execution(**overrides: object) -> ExecutionCreate:
    payload = {
        "automation_name": "invoice-processing",
        "status": "success",
        "duration_seconds": 60,
        "retry_count": 0,
        "environment": "dev",
    }
    payload.update(overrides)
    return ExecutionCreate(**payload)


def test_low_risk_prediction() -> None:
    prediction = predict_failure_risk(make_execution())

    assert prediction.risk_level == "low"
    assert prediction.risk_score < 35
    assert prediction.probable_causes


def test_medium_risk_prediction() -> None:
    prediction = predict_failure_risk(
        make_execution(
            status="partial",
            duration_seconds=420,
            retry_count=0,
            environment="staging",
        )
    )

    assert prediction.risk_level == "medium"


def test_high_risk_prediction() -> None:
    prediction = predict_failure_risk(
        make_execution(
            status="failed",
            duration_seconds=950,
            retry_count=1,
            environment="dev",
        )
    )

    assert prediction.risk_level == "high"


def test_critical_risk_prediction() -> None:
    prediction = predict_failure_risk(
        make_execution(
            status="timeout",
            duration_seconds=1900,
            retry_count=5,
            error_type="network",
            error_message="Connection unavailable from provider gateway",
            environment="production",
        )
    )

    assert prediction.risk_level == "critical"
    assert prediction.risk_score == 100
