import os

from sqlalchemy import func

from app.db import SessionLocal, Base, engine
from app import models
from app.models import User
from app.phone import normalise_phone
from app.security import hash_password

Base.metadata.create_all(engine)
db = SessionLocal()

try:
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin or not admin.email or not admin.phone or not admin.password_hash:
        email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        password = os.getenv("ADMIN_PASSWORD", "")
        raw_phone = os.getenv("ADMIN_PHONE", "").strip()
        if not email or not password or not raw_phone:
            raise RuntimeError(
                "Set ADMIN_EMAIL, ADMIN_PASSWORD, and ADMIN_PHONE before seeding an admin account."
            )

        phone = normalise_phone(raw_phone)
        email_query = db.query(User).filter(func.lower(User.email) == email)
        phone_query = db.query(User).filter(User.phone == phone)
        if admin:
            email_query = email_query.filter(User.id != admin.id)
            phone_query = phone_query.filter(User.id != admin.id)
        if email_query.first():
            raise RuntimeError("ADMIN_EMAIL is already assigned to another account.")
        if phone_query.first():
            raise RuntimeError("ADMIN_PHONE is already assigned to another account.")
        if admin and admin.email and admin.email.strip().lower() != email:
            raise RuntimeError(
                "ADMIN_EMAIL must match the existing admin account's email."
            )

        if admin is None:
            admin = User(role="admin", full_name="Admin")
            db.add(admin)
        admin.email = email
        admin.phone = phone
        admin.password_hash = hash_password(password)

    if not db.query(User).filter(User.role == "consultant").first():
        db.add_all([
            User(role="consultant", full_name="Consultant One",
                 phone="+254700000002", password_hash=hash_password("Staff#2026")),
            User(role="consultant", full_name="Consultant Two",
                 phone="+254700000003", password_hash=hash_password("Staff#2026")),
        ])

    db.commit()
    print("Seed data ready")
finally:
    db.close()
