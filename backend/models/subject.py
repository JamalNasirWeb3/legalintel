from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel


class SubjectCreate(BaseModel):
    case_id: UUID
    full_name: str
    country: str = "US"                # e.g. "PK" for Pakistan, "US" for United States
    aliases: list[str] | None = None
    date_of_birth: date | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None   # US state code OR Pakistani province
    address_zip: str | None = None
    ssn_last4: str | None = None
    known_employers: list[str] | None = None
    known_spouses: list[str] | None = None
    known_businesses: list[str] | None = None
    photo_url: str | None = None


class SubjectUpdate(BaseModel):
    full_name: str | None = None
    country: str | None = None
    aliases: list[str] | None = None
    date_of_birth: date | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    ssn_last4: str | None = None
    known_employers: list[str] | None = None
    known_spouses: list[str] | None = None
    known_businesses: list[str] | None = None
    photo_url: str | None = None


class Subject(SubjectCreate):
    id: UUID
    created_at: datetime
