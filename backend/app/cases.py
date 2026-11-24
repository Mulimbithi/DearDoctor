from sqlalchemy.orm import Session

from app.models import User, Referral, RiskEvent

OPEN_STATUSES = ("open", "in follow-up")

def assign_consultant(db: Session, user_id: int):
    """Same consultant if she already has an active one; otherwise the active
    consultant with the fewest open cases. Returns None if nobody is active."""
    last = (db.query(Referral)
            .join(RiskEvent, Referral.risk_event_id == RiskEvent.id)
            .filter(RiskEvent.user_id == user_id,
                    Referral.consultant_id.isnot(None))
                    .order_by(Referral.id.desc())
                    .first())
    if last:
        previous = db.get(User, last.consultant_id)
        if previous and previous.role == "consultant" and previous.status == "active":
            return previous.id
    consultants = (db.query(User)
                   .filter(User.role == "consultant", User.status == "active")
                   .all())
    if not consultants:
        return None
    def open_count(c):
        return (db.query(Referral)
                .filter(Referral.consultant_id == c.id,
                        Referral.status.in_(OPEN_STATUSES))
                .count())
    return min(consultants, key=open_count).id
def open_case(db: Session, user_id: int, screening_id, level: str, trigger: str):
    """Saves a risk event. If she already has an open case, the new result is
    added to it; otherwise a new referral is created and assigned."""
    risk = RiskEvent(user_id=user_id, screening_id=screening_id,
                     level=level, trigger=trigger)
    db.add(risk)
    db.flush()

    existing = (db.query(Referral)
                .join(RiskEvent, Referral.risk_event_id == RiskEvent.id)
                .filter(RiskEvent.user_id == user_id,
                        Referral.status.in_(OPEN_STATUSES))
                .order_by(Referral.id.desc())
                .first())
    if existing:
        # same case, now showing her newest result
        existing.risk_event_id = risk.id
        db.commit()
        return existing

    consultant_id = assign_consultant(db, user_id)
    referral = Referral(risk_event_id=risk.id, consultant_id=consultant_id,
                        status="open")
    db.add(referral)
    db.commit()
    # TODO Phase 4: queue the SMS alert to the consultant here
    return referral