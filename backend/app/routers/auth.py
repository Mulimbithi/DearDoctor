#checks what the OTP depends on
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, OtpCode, Consent
from app.phone import normalise_phone
from app.security import create_token, generate_otp, hash_otp, verify_password, require_role
from app.email_sender import send_otp_email

router= APIRouter(prefix="/api/auth", tags=["auth"])

class OtpRequestIn(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        return normalise_phone(v)

class OtpVerifyIn(BaseModel):
    phone: str
    code: str

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        return normalise_phone(v)

def find_user(db: Session, phone: str):
    return(db.query(User)
           .filter(User.phone  == phone,
                   User.status == "active")
            .first())

def request_otp(data: OtpRequestIn, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    user = find_user(db, data.phone)
    if user:
        # codes last 5 min, so expires_at after now-10min means created in the last 15 min
        recent = (db.query(OtpCode)
                    .filter(OtpCode.user_id == user.id,
                            OtpCode.expires_at > now - timedelta(minutes=10))
                    .count())
        if recent >= 3:
            raise HTTPException(status_code=429,
                                detail="Too many requests. Try again later.")
        code = generate_otp()
        print(f"OTP for {data.phone}: {code}", flush=True)
        db.add(OtpCode(user_id=user.id, code_hash=hash_otp(code),
                       expires_at=now + timedelta(minutes=5)))
        db.commit()
        print(f"OTP for {data.phone}: {code}", flush=True)  # Phase 4 replaces this with an SMS
        if user.email:
            send_otp_email(user.email, code)

    return {"message": "If the number is registered, a code has been sent."}
class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    user = (db.query(User)
            .filter(func.lower(User.email) == email, User.status == "active")
            .first())
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    if user.deletion_requested_at:
        requested_at = user.deletion_requested_at
        if requested_at.tzinfo is None:
            requested_at = requested_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) >= requested_at + timedelta(days=7):
            user.status = "deleted"
            user.pseudonym = "Deleted mother"
            user.phone = None
            user.email = None
            user.age_range = None
            user.password_hash = None
            db.query(Consent).filter(Consent.user_id == user.id).delete(synchronize_session=False)
            db.query(OtpCode).filter(OtpCode.user_id == user.id).delete(synchronize_session=False)
            db.commit()
            raise HTTPException(status_code=404, detail="This account has been deleted")
        raise HTTPException(
            status_code=403,
            detail="Account deletion is pending. Sign in with an existing session to cancel it.",
        )

    result = request_otp(OtpRequestIn(phone=user.phone), db)
    return {**result,
            "pending_token": create_token(user.id, "pending"),
            "phone": user.phone}

@router.post("/resend-otp")
def resend_otp(token=Depends(require_role("pending")),
               db: Session = Depends(get_db)):
    user = db.get(User, int(token["sub"]))
    if not user or user.status != "active":
        raise HTTPException(status_code=404, detail="User not found")
    return request_otp(OtpRequestIn(phone=user.phone), db)

@router.post("/verify-otp")
def verify_otp(data: OtpVerifyIn, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    user = find_user(db, data.phone)
    otp = None
    if user:
        otp = (db.query(OtpCode)
               .filter(OtpCode.user_id == user.id,
                       OtpCode.used == False,
                       OtpCode.expires_at > now)
                       .order_by(OtpCode.id.desc())
                       .first())
    if not otp or otp.code_hash != hash_otp(data.code):
        raise HTTPException(status_code=401, detail="Invalid or expired code")
    otp.used = True
    db.commit()
    return{"token": create_token(user.id, user.role), "role":user.role}
        
            
