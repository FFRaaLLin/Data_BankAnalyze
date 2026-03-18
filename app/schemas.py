from datetime import datetime

from pydantic import BaseModel, Field


class UnknownFormItem(BaseModel):
    source_order_id: str = Field(min_length=1, max_length=128)
    source_system: str = Field(min_length=1, max_length=64)
    amount: float
    form_date: str
    raw_payload: dict


class UnknownFormBatchRequest(BaseModel):
    items: list[UnknownFormItem]


class UnknownFormBatchResponse(BaseModel):
    inserted: int


class ExportTaskRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=5000)


class ExportTaskResponse(BaseModel):
    task_id: int
    items: list[dict]


class CallbackItem(BaseModel):
    form_id: int
    category_code: str
    category_name: str
    reviewer: str
    reviewed_at: datetime
    confidence: float | None = None


class CallbackRequest(BaseModel):
    items: list[CallbackItem]


class TaskActionResponse(BaseModel):
    task_id: int
    status: str
    detail: str
