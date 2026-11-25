from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from app.db import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    role = Column(String(20), nullable=False)        # mother / consultant / admin
    pseudonym = Column(String(60))
    full_name = Column(String(100))                  # staff only
    phone = Column(String(20))
    email = Column(String(255))                       # mother: only if she opts in
    age_range = Column(String(20))
    status = Column(String(20), default="active")    # active / paused
    created_at = Column(DateTime(timezone=True), default=now)
    password_hash = Column(String(255))

class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    consent_given = Column(Boolean, default=False)
    sms_opt_in = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now)
    call_consent = Column(Boolean, default=False)

class ChatSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime(timezone=True), default=now)
    ended_at = Column(DateTime(timezone=True))


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    sender = Column(String(10))                      # bot / mother
    text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now)

class Screening(Base):
    __tablename__ = "screenings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("sessions.id"))
    answers = Column(JSON)
    total_score = Column(Integer)
    item10_value = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=now)


class RiskEvent(Base):
    __tablename__ = "risk_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    screening_id = Column(Integer, ForeignKey("screenings.id"), nullable=True)
    level = Column(String(10))                       # urgent / high / none
    trigger = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=now)


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    risk_event_id = Column(Integer, ForeignKey("risk_events.id"))
    consultant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="open")      # open / in follow-up / closed
    assigned_at = Column(DateTime(timezone=True), default=now)


class CaseNote(Base):
    __tablename__ = "case_notes"
    id = Column(Integer, primary_key=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"))
    consultant_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    code_hash = Column(String(128))
    expires_at = Column(DateTime(timezone=True))
    used = Column(Boolean, default=False)

class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"))
    consultant_id = Column(Integer, ForeignKey("users.id"))
    outcome = Column(String(40))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now)