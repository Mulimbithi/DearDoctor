from fastapi import FastAPI
from app.db import engine, Base
from app import models

Base.metadata.create_all(engine)


app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok"}