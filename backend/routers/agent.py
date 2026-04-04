import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from auth import get_current_user
from database import get_client
from models import InvestigationJob
from limiter import limiter

router = APIRouter(prefix="/agent", tags=["agent"])


class RunRequest(BaseModel):
    case_id: UUID
    subject_id: UUID


@router.post("/run", response_model=InvestigationJob, status_code=202)
@limiter.limit("5/minute")
async def run_investigation(
    request: Request,
    body: RunRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    db = get_client()

    # Verify the case belongs to this user
    case_check = (
        db.table("cases")
        .select("id")
        .eq("id", str(body.case_id))
        .eq("user_id", user_id)
        .execute()
    )
    if not case_check.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create the job record
    job_data = {
        "case_id": str(body.case_id),
        "subject_id": str(body.subject_id),
        "status": "pending",
    }
    result = db.table("investigation_jobs").insert(job_data).execute()
    job = result.data[0]

    # Kick off the agent in the background
    background_tasks.add_task(_run_agent, job["id"], str(body.subject_id))

    return job


@router.get("/status/{job_id}", response_model=InvestigationJob)
async def get_job_status(job_id: UUID, user_id: str = Depends(get_current_user)):
    db = get_client()
    result = db.table("investigation_jobs").select("*").eq("id", str(job_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = result.data[0]

    # Verify ownership via the parent case
    case_check = (
        db.table("cases")
        .select("id")
        .eq("id", job["case_id"])
        .eq("user_id", user_id)
        .execute()
    )
    if not case_check.data:
        raise HTTPException(status_code=403, detail="Access denied")

    return job


async def _run_agent(job_id: str, subject_id: str):
    """Background task: runs the investigation agent and updates the job record."""
    db = get_client()

    db.table("investigation_jobs").update({
        "status": "running",
        "started_at": "now()",
    }).eq("id", job_id).execute()

    try:
        from agents.investigator import run_investigation

        subject_result = db.table("subjects").select("*").eq("id", subject_id).execute()
        if not subject_result.data:
            raise ValueError(f"Subject {subject_id} not found")

        subject = subject_result.data[0]
        report_data, raw_findings = await run_investigation(subject)

        db.table("investigation_jobs").update({
            "raw_findings": raw_findings,
        }).eq("id", job_id).execute()

        job_result = db.table("investigation_jobs").select("case_id").eq("id", job_id).execute()
        case_id = job_result.data[0]["case_id"]

        db.table("reports").insert({
            "case_id": case_id,
            "job_id": job_id,
            **report_data,
        }).execute()

        db.table("investigation_jobs").update({
            "status": "complete",
            "completed_at": "now()",
        }).eq("id", job_id).execute()

    except Exception as e:
        msg = str(e)
        if "529" in msg or "overloaded" in msg.lower():
            msg = "The AI API is temporarily overloaded. Please try again in a few minutes."
        elif "429" in msg:
            msg = "Rate limit reached. Please wait a minute before retrying."
        db.table("investigation_jobs").update({
            "status": "failed",
            "error_message": msg,
            "completed_at": "now()",
        }).eq("id", job_id).execute()
        raise
