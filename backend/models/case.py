from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class CaseCreate(BaseModel):
    title: str
    attorney_name: str | None = None
    client_name: str | None = None
    judgment_amount: Decimal | None = None
    notes: str | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    attorney_name: str | None = None
    client_name: str | None = None
    judgment_amount: Decimal | None = None
    notes: str | None = None
    status: str | None = None


class Case(CaseCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str = "open"
