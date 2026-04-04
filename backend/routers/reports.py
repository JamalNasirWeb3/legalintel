from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from auth import get_current_user
from database import get_client
from models import Report
from services.pdf_service import generate_report_pdf
from services.email_service import send_report_email

router = APIRouter(prefix="/reports", tags=["reports"])


def _verify_report_owner(db, report: dict, user_id: str):
    """Raise 403 if the report's parent case doesn't belong to this user."""
    result = (
        db.table("cases")
        .select("id")
        .eq("id", report["case_id"])
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("", response_model=list[Report])
async def list_reports(case_id: UUID | None = None, user_id: str = Depends(get_current_user)):
    db = get_client()
    query = (
        db.table("reports")
        .select("*, cases!inner(user_id)")
        .eq("cases.user_id", user_id)
    )
    if case_id:
        query = query.eq("case_id", str(case_id))
    result = query.order("created_at", desc=True).execute()
    rows = [{k: v for k, v in row.items() if k != "cases"} for row in result.data]
    return rows


@router.get("/{report_id}", response_model=Report)
async def get_report(report_id: UUID, user_id: str = Depends(get_current_user)):
    db = get_client()
    result = db.table("reports").select("*").eq("id", str(report_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")
    report = result.data[0]
    _verify_report_owner(db, report, user_id)
    return report


class EmailReportRequest(BaseModel):
    email: EmailStr
    subject_name: str = "Unknown Subject"


@router.post("/{report_id}/email", status_code=200)
async def email_report(
    report_id: UUID,
    body: EmailReportRequest,
    user_id: str = Depends(get_current_user),
):
    """Generate a PDF from the report and send it to the provided email address."""
    db = get_client()
    result = db.table("reports").select("*").eq("id", str(report_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found")

    report_data = result.data[0]
    _verify_report_owner(db, report_data, user_id)
    report_data["subject_name"] = body.subject_name

    # Attach photo_url from the subject so the PDF can include the debtor's photo
    subject_result = (
        db.table("subjects")
        .select("photo_url")
        .eq("case_id", report_data["case_id"])
        .limit(1)
        .execute()
    )
    if subject_result.data:
        report_data["photo_url"] = subject_result.data[0].get("photo_url")

    try:
        pdf_bytes = generate_report_pdf(report_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    try:
        await send_report_email(
            to_address=body.email,
            subject_name=body.subject_name,
            report_id=str(report_id),
            pdf_bytes=pdf_bytes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {exc}") from exc

    return {"message": f"Report sent to {body.email}"}
