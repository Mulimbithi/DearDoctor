from app.db import SessionLocal
from app.models import User
from app.security import hash_password

db = SessionLocal()
staff = db.query(User).filter(User.role.in_(["admin", "consultant"])).all()
for u in staff:
    u.password_hash = hash_password("Staff#2026")
    print("Password set for", u.phone, u.role)
db.commit()
db.close()
