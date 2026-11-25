from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.chatbot.epds import (total_score, item10_positive,
                              MODERATE_THRESHOLD, HIGH_RISK_THRESHOLD)
from app.email_sender import send_new_case_email
from app.models import Referral, RiskEvent, User


OPEN_STATUSES = ["open", "in follow-up"]


def classify(answers: list) -> str:
    """Returns 'urgent', 'high', 'moderate' or 'low'."""
    if item10_positive(answers):
        return "urgent"
    total = total_score(answers)
    if total >= HIGH_RISK_THRESHOLD:
        return "high"
    if total >= MODERATE_THRESHOLD:
        return "moderate"
    return "low"


def assigns_immediately(level: str) -> bool:
    return level in ("high", "urgent")


def offers_consultant(level: str) -> bool:
    return level in ("low", "moderate")


def open_count(db: Session, consultant_id: int) -> int:
    return (db.query(Referral)
              .filter(Referral.consultant_id == consultant_id,
                      Referral.status.in_(OPEN_STATUSES))
              .count())


def assign_consultant(db: Session):
    """Return the active consultant with the fewest open cases, if any."""
    consultants = (db.query(User)
                     .filter(User.role == "consultant", User.status == "active")
                     .all())
    if not consultants:
        return None
    return min(consultants, key=lambda consultant: open_count(db, consultant.id))


def current_referral(db: Session, user_id: int):
    """Return the user's latest open referral, if one exists."""
    return (db.query(Referral)
              .join(RiskEvent, Referral.risk_event_id == RiskEvent.id)
              .filter(RiskEvent.user_id == user_id,
                      Referral.status.in_(OPEN_STATUSES))
              .order_by(Referral.id.desc())
              .first())


def open_case(db: Session, user_id: int, screening_id: int | None,
              level: str, trigger: str) -> tuple[Referral, bool]:
    """Record a risk event and open or update the user's referral."""
    risk_event = RiskEvent(user_id=user_id, screening_id=screening_id,
                           level=level, trigger=trigger)
    db.add(risk_event)
    db.flush()

    existing = current_referral(db, user_id)
    if existing:
        existing.risk_event_id = risk_event.id
        db.flush()
        return existing, False

    consultant = assign_consultant(db)
    referral = Referral(risk_event_id=risk_event.id,
                        consultant_id=consultant.id if consultant else None,
                        status="open",
                        assigned_at=datetime.now(timezone.utc))
    db.add(referral)
    db.flush()
    return referral, True


def notify_assigned_consultant(db: Session, referral: Referral) -> bool:
    if not referral.consultant_id:
        return False
    consultant = db.get(User, referral.consultant_id)
    if not consultant or not consultant.email:
        print(f"Could not notify consultant for referral {referral.id}: no email address",
              flush=True)
        return False
    return send_new_case_email(
        consultant.email,
        consultant.full_name or "Consultant",
    )


def counsellor_first_name(db: Session, referral):
    if not referral or not referral.consultant_id:
        return None
    consultant = db.get(User, referral.consultant_id)
    if not consultant or not consultant.full_name:
        return None
    return consultant.full_name.split()[0]


def counsellor_line(db: Session, referral) -> str:
    name = counsellor_first_name(db, referral)
    if name:
        return f"\n\nYour counsellor is {name}. She will contact you soon."
    return "\n\nA counsellor will be assigned to you and will contact you soon."