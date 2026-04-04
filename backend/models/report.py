from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class InvestigationJob(BaseModel):
    id: UUID
    case_id: UUID
    subject_id: UUID
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"
    error_message: str | None = None
    raw_findings: dict | None = None


class Report(BaseModel):
    id: UUID
    case_id: UUID
    job_id: UUID
    created_at: datetime
    court_records: dict | None = None
    property_records: dict | None = None
    business_filings: dict | None = None
    social_media: dict | None = None
    employment: dict | None = None
    family_info: dict | None = None
    executive_summary: str | None = None
    asset_summary: str | None = None
    risk_flags: list[str] | None = None
    full_report_md: str | None = None
    confidence_score: float | None = None
    sources_consulted: list[str] | None = None
