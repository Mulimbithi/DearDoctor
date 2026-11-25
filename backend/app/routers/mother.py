from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models import User, Consent
from app.phone import normalise_phone
from app.security import create_token, hash_password

router = APIRouter(prefix="/api/mother", tags=["mother"])

class RegisterIn(BaseModel):
    pseudonym: str
    age_range: str
    phone: str
    consent: bool
    sms_opt_in: bool = False
    password: str
    call_consent: bool = False
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        v = v.strip().lower()
        if " " in v or "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

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
    if (db.query(User)
          .filter(func.lower(User.pseudonym) == data.pseudonym.lower())
          .first()):
        raise HTTPException(status_code=409,
                            detail="This username is taken. Please choose another.")
    if db.query(User).filter(func.lower(User.email) == data.email).first():
        raise HTTPException(status_code=409, detail="That email is already registered")

    user = User(role="mother", pseudonym=data.pseudonym, age_range=data.age_range,
                phone=data.phone, email=data.email,
                password_hash=hash_password(data.password))
    db.add(user)
    db.flush()

    db.add(Consent(user_id=user.id, consent_given=True, sms_opt_in=data.sms_opt_in, call_consent=data.call_consent ))

    db.commit()

    return {"token": create_token(user.id, "mother"), "user_id": user.id}