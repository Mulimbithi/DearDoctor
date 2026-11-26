from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def ensure_schema():
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "deletion_requested_at" not in columns:
            with engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN deletion_requested_at TIMESTAMP WITH TIME ZONE"
                ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
