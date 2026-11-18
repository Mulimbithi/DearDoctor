#creates test consultants and admin
from app.db import SessionLocal, Base, engine
from app import models
from app.models import User

Base.metadata.create_all(engine)
db = SessionLocal()

if not db.query(User).filter(User.role == "admin").first():
    db.add_all([
    User(role="admin", full_name="Admin", phone="+254700000001"),
    User(role="consultant", full_name="Consultant One", phone="+254700000002"),
    User(role="consultant", full_name="Consultant Two", phone="+254700000003"),
])
    db.commit()
    print("Staff created")
else:
    print("Staff already exists")
db.close()