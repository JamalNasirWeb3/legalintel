from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import get_client
from models import Case, CaseCreate, CaseUpdate

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[Case])
async def list_cases(user_id: str = Depends(get_current_user)):
    db = get_client()
    result = (
        db.table("cases")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.post("", response_model=Case, status_code=201)
async def create_case(body: CaseCreate, user_id: str = Depends(get_current_user)):
    db = get_client()
    data = body.model_dump(exclude_none=True)
    data["user_id"] = user_id
    result = db.table("cases").insert(data).execute()
    return result.data[0]


@router.get("/{case_id}", response_model=Case)
async def get_case(case_id: UUID, user_id: str = Depends(get_current_user)):
    db = get_client()
    result = (
        db.table("cases")
        .select("*")
        .eq("id", str(case_id))
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    return result.data[0]


@router.patch("/{case_id}", response_model=Case)
async def update_case(case_id: UUID, body: CaseUpdate, user_id: str = Depends(get_current_user)):
    db = get_client()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = (
        db.table("cases")
        .update(updates)
        .eq("id", str(case_id))
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Case not found")
    return result.data[0]


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: UUID, user_id: str = Depends(get_current_user)):
    db = get_client()
    db.table("cases").delete().eq("id", str(case_id)).eq("user_id", user_id).execute()
