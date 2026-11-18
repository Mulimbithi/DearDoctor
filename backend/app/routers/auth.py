#checks what the OTP depends on
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, OtpCode
from app.phone import normalise_phone
from app.security import create_token, generate_otp, hash_otp

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
@router.post("/request-otp")
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
        db.add(OtpCode(user_id=user.id, code_hash=hash_otp(code),
                       expires_at=now + timedelta(minutes=5)))
        db.commit()
        print(f"OTP for {data.phone}: {code}")   # Phase 4 replaces this with an SMS
    return {"message": "If the number is registered, a code has been sent."}
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
        
            
