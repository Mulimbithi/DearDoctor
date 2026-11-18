from fastapi import FastAPI, Depends
from app.db import engine, Base
from app import models
from app.routers import mother, auth
from app.security import require_role

Base.metadata.create_all(engine)

app = FastAPI()
app.include_router(mother.router)
app.include_router(auth.router)

@app.get("/api/health")
def health():
    return{"status": "ok"}

@app.get("/api/me")
def me(user=Depends(require_role("mother"))):
    return user

@app.get("/api/consultant/ping")#makes the consultants appear under auth in fastAPI
def ping(user=Depends(require_role("consultant"))):
    return{"hello": "consultant"}



