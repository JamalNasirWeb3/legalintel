from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import get_client
from models import Subject, SubjectCreate, SubjectUpdate

router = APIRouter(prefix="/subjects", tags=["subjects"])

print(">>> subjects router loaded (v4 — auth) <<<")


def _verify_case_owner(db, case_id: str, user_id: str):
    """Raise 403 if the case doesn't belong to this user."""
    result = (
        db.table("cases")
        .select("id")
        .eq("id", case_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=403, detail="Access denied")


def _set_country(db, subject_id: str, country: str):
    """Write country via RPC — bypasses PostgREST schema cache."""
    try:
        result = db.rpc("set_subject_country", {
            "p_subject_id": subject_id,
            "p_country": country,
        }).execute()
        print(f">>> set_country({country}) result: {result.data}")
    except Exception as e:
        print(f">>> set_country ERROR: {e}")
        raise


@router.get("", response_model=list[Subject])
async def list_subjects(case_id: UUID | None = None, user_id: str = Depends(get_current_user)):
    try:
        db = get_client()
        query = db.table("subjects").select("*, cases!inner(user_id)")
        query = query.eq("cases.user_id", user_id)
        if case_id:
            query = query.eq("case_id", str(case_id))
        result = query.order("created_at", desc=True).execute()
        # Strip the joined cases column from each row
        rows = [{k: v for k, v in row.items() if k != "cases"} for row in result.data]
        return rows
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post("", response_model=Subject, status_code=201)
async def create_subject(body: SubjectCreate, user_id: str = Depends(get_current_user)):
    db = get_client()
    _verify_case_owner(db, str(body.case_id), user_id)

    country = body.country
    print(f">>> CREATE: country from Pydantic body = '{country}'")

    data = body.model_dump(exclude_none=True)
    data["case_id"] = str(data["case_id"])
    if "date_of_birth" in data and data["date_of_birth"]:
        data["date_of_birth"] = str(data["date_of_birth"])

    result = db.table("subjects").insert(data).execute()
    subject_id = result.data[0]["id"]
    print(f">>> INSERT done, id={subject_id}")

    _set_country(db, subject_id, country)

    fetch = db.table("subjects").select("*").eq("id", subject_id).execute()
    subject = fetch.data[0]
    subject["country"] = country
    print(f">>> RETURNING country='{subject['country']}'")
    return subject


@router.get("/{subject_id}", response_model=Subject)
async def get_subject(subject_id: UUID, user_id: str = Depends(get_current_user)):
    db = get_client()
    result = db.table("subjects").select("*").eq("id", str(subject_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject = result.data[0]
    _verify_case_owner(db, subject["case_id"], user_id)
    return subject


@router.patch("/{subject_id}", response_model=Subject)
async def update_subject(subject_id: UUID, body: SubjectUpdate, user_id: str = Depends(get_current_user)):
    db = get_client()

    # Verify ownership
    fetch_sub = db.table("subjects").select("case_id").eq("id", str(subject_id)).execute()
    if not fetch_sub.data:
        raise HTTPException(status_code=404, detail="Subject not found")
    _verify_case_owner(db, fetch_sub.data[0]["case_id"], user_id)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "date_of_birth" in updates and updates["date_of_birth"]:
        updates["date_of_birth"] = str(updates["date_of_birth"])

    country = updates.get("country")
    print(f">>> PATCH: country from Pydantic body = '{country}', updates = {updates}")

    db.table("subjects").update(updates).eq("id", str(subject_id)).execute()

    if country is not None:
        _set_country(db, str(subject_id), country)

    fetch = db.table("subjects").select("*").eq("id", str(subject_id)).execute()
    if not fetch.data:
        raise HTTPException(status_code=404, detail="Subject not found")
    subject = fetch.data[0]
    subject["country"] = country if country is not None else subject.get("country")
    print(f">>> RETURNING country='{subject['country']}'")
    return subject


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(subject_id: UUID, user_id: str = Depends(get_current_user)):
    db = get_client()
    fetch_sub = db.table("subjects").select("case_id").eq("id", str(subject_id)).execute()
    if fetch_sub.data:
        _verify_case_owner(db, fetch_sub.data[0]["case_id"], user_id)
    db.table("subjects").delete().eq("id", str(subject_id)).execute()
