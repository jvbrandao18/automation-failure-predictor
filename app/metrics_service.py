from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ExecutionRecord
from app.schemas import MetricsResponse


def get_metrics(db: Session) -> MetricsResponse:
    total = db.scalar(select(func.count(ExecutionRecord.id))) or 0

    status_rows = db.execute(
        select(ExecutionRecord.status, func.count(ExecutionRecord.id)).group_by(ExecutionRecord.status)
    ).all()
    risk_rows = db.execute(
        select(ExecutionRecord.risk_level, func.count(ExecutionRecord.id)).group_by(ExecutionRecord.risk_level)
    ).all()
    average_risk = db.scalar(select(func.avg(ExecutionRecord.risk_score))) or 0

    return MetricsResponse(
        total_executions=total,
        counts_by_status={status: count for status, count in status_rows},
        counts_by_risk_level={risk_level: count for risk_level, count in risk_rows},
        average_risk_score=round(float(average_risk), 2),
    )
