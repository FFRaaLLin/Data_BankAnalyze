from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UnknownFormItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_date: str = Field(alias="Transaction Date")
    bank: str = Field(alias="银行", min_length=1, max_length=64)
    bank_account: str = Field(alias="银行账户", min_length=1, max_length=128)
    flow_type: str = Field(alias="收支类型", min_length=1, max_length=32)
    counterparty_account: str = Field(alias="对方账户", min_length=1, max_length=128)
    transaction_details: str = Field(alias="Transaction Details", min_length=1, max_length=512)
    withdrawals: float = Field(alias="Withdrawals", ge=0)
    lodgment: float = Field(alias="Lodgment", ge=0)


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
