from app.db import SessionLocal
from app.models import User
from app.security import hash_password

db = SessionLocal()
for u in db.query(User).filter(User.role == "mother",
                               User.password_hash.is_(None)).all():
    u.password_hash = hash_password("Mother#2026")
    print("Password set for", u.pseudonym)
db.commit()
db.close()