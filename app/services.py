from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ClassificationResult, RetryLog, SyncTask, UnknownForm
from app.schemas import CallbackRequest, UnknownFormBatchRequest


def insert_unknown_forms(db: Session, payload: UnknownFormBatchRequest) -> int:
    rows = [
        UnknownForm(
            source_order_id=item.source_order_id,
            source_system=item.source_system,
            amount=item.amount,
            form_date=item.form_date,
            raw_payload=item.raw_payload,
            status="pending",
        )
        for item in payload.items
    ]
    db.add_all(rows)
    db.commit()
    return len(rows)


def create_export_task(db: Session, limit: int) -> tuple[SyncTask, list[dict]]:
    stmt = (
        select(UnknownForm)
        .where(UnknownForm.status.in_(["pending", "failed"]))
        .order_by(UnknownForm.id.asc())
        .limit(limit)
    )
    forms = db.scalars(stmt).all()
    items = [
        {
            "form_id": f.id,
            "source_order_id": f.source_order_id,
            "source_system": f.source_system,
            "amount": float(f.amount),
            "form_date": f.form_date,
            "raw_payload": f.raw_payload,
        }
        for f in forms
    ]

    task = SyncTask(task_type="export", status="pushed", payload={"items": items})
    db.add(task)

    for form in forms:
        form.status = "in_sync"
        form.last_error = None

    db.commit()
    db.refresh(task)
    return task, items


def process_callback(db: Session, task_id: int, request: CallbackRequest) -> tuple[str, str]:
    task = db.get(SyncTask, task_id)
    if not task:
        return "not_found", "task not found"

    try:
        for item in request.items:
            form = db.get(UnknownForm, item.form_id)
            if not form:
                raise ValueError(f"form_id={item.form_id} does not exist")

            existing = db.scalar(
                select(ClassificationResult).where(ClassificationResult.form_id == item.form_id)
            )
            if existing:
                existing.category_code = item.category_code
                existing.category_name = item.category_name
                existing.reviewer = item.reviewer
                existing.reviewed_at = item.reviewed_at
                existing.confidence = item.confidence
            else:
                db.add(
                    ClassificationResult(
                        form_id=item.form_id,
                        category_code=item.category_code,
                        category_name=item.category_name,
                        reviewer=item.reviewer,
                        reviewed_at=item.reviewed_at,
                        confidence=item.confidence,
                    )
                )
            form.status = "resolved"
            form.last_error = None

        task.status = "callback_success"
        task.callback_payload = request.model_dump(mode="json")
        task.error_message = None
        db.commit()
        return "ok", "callback processed"

    except Exception as exc:  # noqa: BLE001
        task.status = "callback_failed"
        task.retry_count += 1
        task.error_message = str(exc)
        retry_no = task.retry_count
        if retry_no >= settings.retry_max_times:
            task.next_retry_at = None
        else:
            task.next_retry_at = datetime.utcnow() + timedelta(minutes=5 * retry_no)
        db.add(RetryLog(task_id=task.id, retry_no=retry_no, reason=str(exc)))
        db.commit()
        return "failed", f"callback failed: {exc}"


def retry_task(db: Session, task_id: int) -> tuple[str, str]:
    task = db.get(SyncTask, task_id)
    if not task:
        return "not_found", "task not found"

    if task.status != "callback_failed":
        return "ignored", "task is not in callback_failed state"

    task.status = "pushed"
    task.next_retry_at = None
    task.error_message = None
    db.commit()
    return "ok", "task reset and ready for reprocessing"
