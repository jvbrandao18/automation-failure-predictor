from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.metrics_service import get_metrics
from app.models import ExecutionRecord
from app.prediction_service import predict_failure_risk
from app.schemas import ExecutionCreate, ExecutionResponse, MetricsResponse, PredictionResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Automation Failure Predictor",
    description="Rule-based failure risk scoring for automation execution records.",
    version="1.0.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Automation Failure Predictor",
        "description": "FastAPI backend for transparent automation failure risk scoring.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(execution: ExecutionCreate) -> PredictionResponse:
    return predict_failure_risk(execution)


@app.post("/executions", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
def create_execution(execution: ExecutionCreate, db: Session = Depends(get_db)) -> ExecutionRecord:
    prediction = predict_failure_risk(execution)
    db_record = ExecutionRecord(
        **execution.model_dump(),
        risk_score=prediction.risk_score,
        risk_level=prediction.risk_level,
        probable_causes=prediction.probable_causes,
        recommended_actions=prediction.recommended_actions,
        explanation=prediction.explanation,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/executions", response_model=list[ExecutionResponse])
def list_executions(db: Session = Depends(get_db)) -> list[ExecutionRecord]:
    return db.query(ExecutionRecord).order_by(ExecutionRecord.created_at.desc()).all()


@app.get("/executions/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: int, db: Session = Depends(get_db)) -> ExecutionRecord:
    execution = db.get(ExecutionRecord, execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return execution


@app.get("/metrics", response_model=MetricsResponse)
def metrics(db: Session = Depends(get_db)) -> MetricsResponse:
    return get_metrics(db)
