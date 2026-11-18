from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, Consent
from app.phone import normalise_phone
from app.security import create_token

router = APIRouter(prefix="/api/mother", tags=["mother"])

class RegisterIn(BaseModel):
    pseudonym: str
    age_range: str
    phone: str
    consent: bool
    sms_opt_in: bool = False

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        return normalise_phone(v)

@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if not data.consent:
        raise HTTPException(status_code=400, detail="Consent is required")
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=409,
                            detail="This number is already registered. Please sign in.")
    user = User(role="mother", pseudonym=data.pseudonym, age_range=data.age_range, phone=data.phone)
    db.add(user)
    db.flush()

    db.add(Consent(user_id=user.id, consent_given=True, sms_opt_in=data.sms_opt_in))

    db.commit()

    return {"token": create_token(user.id, "mother"), "user_id": user.id}