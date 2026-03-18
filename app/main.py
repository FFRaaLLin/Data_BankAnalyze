from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.schemas import (
    CallbackRequest,
    ExportTaskRequest,
    ExportTaskResponse,
    TaskActionResponse,
    UnknownFormBatchRequest,
    UnknownFormBatchResponse,
)
from app.services import create_export_task, insert_unknown_forms, process_callback, retry_task

app = FastAPI(title="Unknown Form Classification Service", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.post("/unknown-forms/batch", response_model=UnknownFormBatchResponse)
def batch_insert_unknown_forms(
    payload: UnknownFormBatchRequest, db: Session = Depends(get_db)
) -> UnknownFormBatchResponse:
    inserted = insert_unknown_forms(db, payload)
    return UnknownFormBatchResponse(inserted=inserted)


@app.post("/sync/tasks/export", response_model=ExportTaskResponse)
def new_export_task(
    payload: ExportTaskRequest, db: Session = Depends(get_db)
) -> ExportTaskResponse:
    task, items = create_export_task(db, payload.limit)
    return ExportTaskResponse(task_id=task.id, items=items)


@app.post("/sync/tasks/{task_id}/callback", response_model=TaskActionResponse)
def callback_result(
    task_id: int, payload: CallbackRequest, db: Session = Depends(get_db)
) -> TaskActionResponse:
    status, detail = process_callback(db, task_id, payload)
    return TaskActionResponse(task_id=task_id, status=status, detail=detail)


@app.post("/sync/tasks/{task_id}/retry", response_model=TaskActionResponse)
def manual_retry(task_id: int, db: Session = Depends(get_db)) -> TaskActionResponse:
    status, detail = retry_task(db, task_id)
    return TaskActionResponse(task_id=task_id, status=status, detail=detail)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}
