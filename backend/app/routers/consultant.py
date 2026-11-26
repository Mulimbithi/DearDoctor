from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CaseNote, Consent, Referral, RiskEvent, Screening, User
from app.security import require_role

router = APIRouter(prefix="/api/consultant", tags=["consultant"])

MAX_CASES = 4


def fmt(dt):
    return dt.strftime("%Y-%m-%d") if dt else ""


def my_referral(db: Session, token, ref: str) -> Referral:
    """Find a case by its reference (like C-12). It must belong to this consultant."""
    try:
        referral_id = int(ref.removeprefix("C-"))
    except ValueError:
        raise HTTPException(status_code=404, detail="Case not found")
    referral = db.get(Referral, referral_id)
    if not referral or referral.consultant_id != int(token["sub"]):
        raise HTTPException(status_code=404, detail="Case not found")
    return referral


def has_call_consent(db: Session, user_id: int) -> bool:
    consent = (db.query(Consent)
                 .filter(Consent.user_id == user_id)
                 .order_by(Consent.id.desc())
                 .first())
    return bool(consent and consent.call_consent)


def summary(db: Session, referral: Referral) -> dict:
    event = db.get(RiskEvent, referral.risk_event_id)
    mother = db.get(User, event.user_id)
    return {
        "ref": f"C-{referral.id}",
        "risk": event.level.capitalize(),
        "nickname": mother.pseudonym,
        "age_range": mother.age_range,
        "status": referral.status,
        "assigned_at": fmt(referral.assigned_at),
    }


class NoteIn(BaseModel):
    body: str


@router.get("/cases")
def list_cases(token=Depends(require_role("consultant")),
               db: Session = Depends(get_db)):
    referrals = (db.query(Referral)
                   .filter(Referral.consultant_id == int(token["sub"]),
                           Referral.status != "closed")
                   .order_by(Referral.assigned_at)
                   .all())
    return {"max_cases": MAX_CASES,
            "cases": [summary(db, r) for r in referrals],
            "notices": []}


@router.get("/cases/{ref}")
def case_detail(ref: str, token=Depends(require_role("consultant")),
                db: Session = Depends(get_db)):
    referral = my_referral(db, token, ref)
    event = db.get(RiskEvent, referral.risk_event_id)
    screening = db.get(Screening, event.screening_id) if event.screening_id else None

    data = summary(db, referral)
    data["score"] = screening.total_score if screening else None
    data["self_harm"] = bool(screening and screening.item10_value
                             and screening.item10_value > 0)
    data["trigger"] = event.trigger
    data["call_consent"] = has_call_consent(db, event.user_id)

    notes = (db.query(CaseNote)
               .filter(CaseNote.referral_id == referral.id)
               .order_by(CaseNote.created_at)
               .all())
    data["notes"] = [{"author": "You",
                      "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
                      "body": n.note} for n in notes]

    return data


@router.post("/cases/{ref}/notes", status_code=201)
def add_note(ref: str, data: NoteIn,
             token=Depends(require_role("consultant")),
             db: Session = Depends(get_db)):
    referral = my_referral(db, token, ref)
    if referral.status == "closed":
        raise HTTPException(status_code=409, detail="Case is closed")
    text = data.body.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Note is empty")
    db.add(CaseNote(referral_id=referral.id,
                    consultant_id=int(token["sub"]), note=text))
    if referral.status == "open":
        referral.status = "in follow-up"
    db.commit()
    return {"status": "ok"}


@router.patch("/cases/{ref}/close")
def close_case(ref: str, token=Depends(require_role("consultant")),
               db: Session = Depends(get_db)):
    referral = my_referral(db, token, ref)
    referral.status = "closed"
    db.commit()
    return {"status": "ok"}