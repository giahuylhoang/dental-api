"""GET/PUT /api/portal/clinics/{cid}/greeting — stored as JSONB on clinics table."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import Clinic

router = APIRouter()


class GreetingBody(BaseModel):
    greeting: Dict[str, Any] = {}


@router.get("", response_model=GreetingBody)
def get_greeting(clinic_id: str, db: Session = Depends(get_db)) -> GreetingBody:
    c = db.query(Clinic).filter_by(id=clinic_id).first()
    if c is None:
        raise HTTPException(404, "clinic_not_found")
    return GreetingBody(greeting=(c.greeting or {}))


@router.put("", response_model=GreetingBody)
def put_greeting(clinic_id: str, body: GreetingBody, db: Session = Depends(get_db)) -> GreetingBody:
    c = db.query(Clinic).filter_by(id=clinic_id).first()
    if c is None:
        raise HTTPException(404, "clinic_not_found")
    c.greeting = body.greeting
    db.commit()
    db.refresh(c)
    return GreetingBody(greeting=c.greeting)
