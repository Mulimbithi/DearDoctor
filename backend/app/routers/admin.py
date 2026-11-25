import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.chatbot.risk import OPEN_STATUSES, open_count
from app.db import get_db
from app.email_sender import send_email
from app.models import Referral, User
from app.phone import normalise_phone
from app.security import hash_password, require_role

router = APIRouter(prefix="/api/admin", tags=["admin"])


def consultant_row(db: Session, u: User) -> dict:
    return {"id": u.id,
            "name": u.full_name or "(no name)",
            "email": u.email or "",
            "status": u.status,
            "open_cases": open_count(db, u.id)}


def get_consultant(db: Session, user_id: int) -> User:
    u = db.get(User, user_id)
    if not u or u.role != "consultant":
        raise HTTPException(status_code=404, detail="Consultant not found")
    return u


def send_consultant_invite(db: Session, consultant: User) -> bool:
    temp_password = secrets.token_urlsafe(9)
    consultant.password_hash = hash_password(temp_password)
    db.add(consultant)
    db.commit()

    return send_email(
        consultant.email,
        "Your DearDoctor consultant account",
        f"Hello {consultant.full_name},\n\n"
        "An account has been created for you on DearDoctor.\n"
        f"Email: {consultant.email}\n"
        f"Temporary password: {temp_password}\n\n"
        "Sign in with your email and this password. A code will then be sent to your email.",
    )


class ConsultantIn(BaseModel):
    name: str
    email: str
    phone: str

    @field_validator("name")
    @classmethod
    def check_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        v = v.strip().lower()
        if " " in v or "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        return normalise_phone(v)


@router.get("/consultants")
def list_consultants(token=Depends(require_role("admin")),
                     db: Session = Depends(get_db)):
    users = (db.query(User)
               .filter(User.role == "consultant")
               .order_by(User.full_name)
               .all())
    return {"consultants": [consultant_row(db, u) for u in users],
            "notices": []}


@router.post("/consultants", status_code=201)
def create_consultant(data: ConsultantIn,
                      token=Depends(require_role("admin")),
                      db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == data.email).first():
        raise HTTPException(status_code=409, detail="That email is already registered")
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=409, detail="That phone number is already registered")

    user = User(role="consultant", full_name=data.name, email=data.email,
                phone=data.phone, status="active")
    db.add(user)
    db.flush()
    sent = send_consultant_invite(db, user)
    return {"consultant": consultant_row(db, user), "invite_sent": sent}


@router.post("/consultants/{user_id}/invite")
def retry_consultant_invite(user_id: int,
                            token=Depends(require_role("admin")),
                            db: Session = Depends(get_db)):
    consultant = get_consultant(db, user_id)
    if not consultant.email:
        raise HTTPException(status_code=400, detail="Consultant has no email address")
    sent = send_consultant_invite(db, consultant)
    return {"invite_sent": sent}


@router.post("/consultants/{user_id}/pause")
def pause_consultant(user_id: int,
                     token=Depends(require_role("admin")),
                     db: Session = Depends(get_db)):
    u = get_consultant(db, user_id)
    u.status = "paused"
    db.flush()

    # takeover: her open cases move to the active consultants with the fewest open cases
    others = (db.query(User)
                .filter(User.role == "consultant", User.status == "active",
                        User.id != u.id)
                .all())
    moved = 0
    if others:
        open_cases = (db.query(Referral)
                        .filter(Referral.consultant_id == u.id,
                                Referral.status.in_(OPEN_STATUSES))
                        .all())
        for case in open_cases:
            target = min(others, key=lambda c: open_count(db, c.id))
            case.consultant_id = target.id
            db.flush()
            moved += 1
    db.commit()

    row = consultant_row(db, u)
    row["reassigned"] = moved
    return row


@router.post("/consultants/{user_id}/reactivate")
def reactivate_consultant(user_id: int,
                          token=Depends(require_role("admin")),
                          db: Session = Depends(get_db)):
    u = get_consultant(db, user_id)
    u.status = "active"
    db.commit()
    return consultant_row(db, u)