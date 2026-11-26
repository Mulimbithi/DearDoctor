from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models import User, Consent, OtpCode
from app.phone import normalise_phone
from app.security import hash_password, require_role, verify_password

router = APIRouter(prefix="/api/mother", tags=["mother"])

DELETION_WAIT_DAYS = 7


class DeletionIn(BaseModel):
    password: str


def get_mother(db: Session, token: dict) -> User:
    user = db.get(User, int(token["sub"]))
    if not user or user.role != "mother" or user.status not in ("active", "deleted"):
        raise HTTPException(status_code=404, detail="Account not found")
    if user.status == "deleted":
        raise HTTPException(status_code=404, detail="Account not found")
    return user


def requested_at_is_aware(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def anonymize_deleted_account(db: Session, user: User) -> None:
    user.status = "deleted"
    user.pseudonym = "Deleted mother"
    user.phone = None
    user.email = None
    user.age_range = None
    user.password_hash = None
    user.deletion_requested_at = datetime.now(timezone.utc)
    db.query(Consent).filter(Consent.user_id == user.id).delete(synchronize_session=False)
    db.query(OtpCode).filter(OtpCode.user_id == user.id).delete(synchronize_session=False)
    db.add(user)


@router.get("/deletion-request")
def get_deletion_request(token=Depends(require_role("mother")),
                         db: Session = Depends(get_db)):
    user = get_mother(db, token)
    requested_at = requested_at_is_aware(user.deletion_requested_at)
    if requested_at:
        if datetime.now(timezone.utc) >= requested_at + timedelta(days=DELETION_WAIT_DAYS):
            anonymize_deleted_account(db, user)
            db.commit()
            return {
                "pending": False,
                "deleted": True,
                "message": "Your account has been deleted."
            }
        return {
            "pending": True,
            "deleted": False,
            "message": "Your deletion request is pending. You can cancel it during the 7-day waiting period."
        }
    return {"pending": False, "deleted": False, "message": "No deletion request is pending."}


@router.post("/deletion-request")
def request_deletion(data: DeletionIn,
                     token=Depends(require_role("mother")),
                     db: Session = Depends(get_db)):
    user = get_mother(db, token)
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
    if user.deletion_requested_at is not None:
        raise HTTPException(status_code=409, detail="A deletion request is already pending")

    user.deletion_requested_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "pending": True,
        "message": "Your request was received. Your account will be deleted after 7 days. You can cancel during the waiting period."
    }


@router.post("/deletion-request/cancel")
def cancel_deletion_request(token=Depends(require_role("mother")),
                            db: Session = Depends(get_db)):
    user = get_mother(db, token)
    if user.deletion_requested_at is None:
        return {"pending": False, "message": "There is no deletion request to cancel."}

    requested_at = requested_at_is_aware(user.deletion_requested_at)
    if requested_at and datetime.now(timezone.utc) >= requested_at + timedelta(days=DELETION_WAIT_DAYS):
        anonymize_deleted_account(db, user)
        db.commit()
        return {"pending": False, "deleted": True,
                "message": "The 7-day waiting period has ended, so the account has been deleted."}

    user.status = "active"
    user.deletion_requested_at = None
    db.commit()
    return {"pending": False, "message": "Your deletion request has been cancelled."}

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

    return {"user_id": user.id, "message": "Account created. Please sign in."}