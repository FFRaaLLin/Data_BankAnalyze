from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UnknownForm(Base):
    __tablename__ = "unknown_forms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    transaction_date: Mapped[str] = mapped_column(String(32), nullable=False)
    bank: Mapped[str] = mapped_column(String(64), nullable=False)
    bank_account: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    flow_type: Mapped[str] = mapped_column(String(32), nullable=False)
    counterparty_account: Mapped[str] = mapped_column(String(128), nullable=False)
    transaction_details: Mapped[str] = mapped_column(String(512), nullable=False)
    withdrawals: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    lodgment: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    last_error: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    classifications = relationship("ClassificationResult", back_populates="form")


class SyncTask(Base):
    __tablename__ = "sync_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False, default="export")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    callback_payload: Mapped[dict | None] = mapped_column(JSON)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[str | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ClassificationResult(Base):
    __tablename__ = "classification_results"
    __table_args__ = (UniqueConstraint("form_id", name="uk_classification_form"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("unknown_forms.id"), nullable=False)
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    category_name: Mapped[str] = mapped_column(String(128), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewed_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())

    form = relationship("UnknownForm", back_populates="classifications")


class RetryLog(Base):
    __tablename__ = "retry_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("sync_tasks.id"), nullable=False)
    retry_no: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())
