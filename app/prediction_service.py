from app.schemas import ExecutionCreate, PredictionResponse, RiskLevel


KNOWN_ERROR_WEIGHTS = {
    "timeout": 20,
    "network": 15,
    "selector": 15,
    "authentication": 20,
    "permission": 20,
    "data_validation": 10,
    "system": 15,
    "dependency": 20,
}


def predict_failure_risk(execution: ExecutionCreate) -> PredictionResponse:
    score = 5
    causes: list[str] = []
    actions: list[str] = []

    status_score = {
        "success": 0,
        "partial": 25,
        "failed": 45,
        "timeout": 55,
    }[execution.status]
    score += status_score

    if execution.status == "timeout":
        causes.append("Execution ended by timeout.")
        actions.append("Review timeout thresholds, external system latency, and long-running steps.")
    elif execution.status == "failed":
        causes.append("Execution finished with a failure status.")
        actions.append("Inspect logs and validate the failing step before the next production run.")
    elif execution.status == "partial":
        causes.append("Execution completed only part of the expected workflow.")
        actions.append("Check partial outputs and confirm whether downstream systems need correction.")
    else:
        causes.append("Execution completed successfully.")

    if execution.retry_count >= 5:
        score += 30
        causes.append("Retry count is very high.")
        actions.append("Investigate recurring transient errors and add a permanent fix before rerunning.")
    elif execution.retry_count >= 3:
        score += 20
        causes.append("Retry count is elevated.")
        actions.append("Review retry logs for unstable dependencies or flaky automation steps.")
    elif execution.retry_count >= 1:
        score += 10
        causes.append("Execution required retries.")
        actions.append("Monitor the automation for repeated retry patterns.")

    if execution.duration_seconds > 1800:
        score += 30
        causes.append("Execution duration is extremely long.")
        actions.append("Profile slow steps and validate upstream system response times.")
    elif execution.duration_seconds > 900:
        score += 20
        causes.append("Execution duration is long.")
        actions.append("Compare the duration with the normal baseline for this automation.")
    elif execution.duration_seconds > 300:
        score += 10
        causes.append("Execution duration is above the expected short-run threshold.")
        actions.append("Watch for gradual performance degradation.")

    normalized_error_type = (execution.error_type or "").strip().lower()
    if normalized_error_type:
        error_weight = KNOWN_ERROR_WEIGHTS.get(normalized_error_type, 10)
        score += error_weight
        causes.append(f"Error type '{normalized_error_type}' is associated with operational risk.")
        actions.append("Classify the error source and confirm whether it is automation, data, or dependency related.")

    message = (execution.error_message or "").lower()
    if any(keyword in message for keyword in ("credential", "login", "unauthorized", "forbidden")):
        score += 10
        causes.append("Error message suggests an access or credential problem.")
        actions.append("Validate service accounts, credentials, and permissions.")
    if any(keyword in message for keyword in ("unavailable", "connection", "503", "gateway")):
        score += 10
        causes.append("Error message suggests an external dependency problem.")
        actions.append("Check dependency health, network stability, and provider incidents.")

    if execution.environment == "production":
        score += 10
        causes.append("Production executions have higher operational severity.")
        actions.append("Prioritize investigation and communicate risk to support stakeholders.")
    elif execution.environment == "staging":
        score += 5
        causes.append("Staging issue may indicate production readiness risk.")
        actions.append("Validate the fix in staging before production deployment.")

    risk_score = min(score, 100)
    risk_level = _risk_level(risk_score)

    explanation = (
        f"Risk score {risk_score}/100 calculated from status='{execution.status}', "
        f"retry_count={execution.retry_count}, duration_seconds={execution.duration_seconds}, "
        f"error_type='{execution.error_type or 'none'}', and environment='{execution.environment}'."
    )

    return PredictionResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        probable_causes=_deduplicate(causes),
        recommended_actions=_deduplicate(actions),
        explanation=explanation,
    )


def _risk_level(score: int) -> RiskLevel:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _deduplicate(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
