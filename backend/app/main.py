from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base, ensure_schema
from app import models
from app.routers import mother, auth, chat, consultant, admin
from app.security import require_role

Base.metadata.create_all(engine)
ensure_schema()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(mother.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(consultant.router)
app.include_router(admin.router)

@app.get("/api/health")
def health():
    return{"status": "ok"}

@app.get("/api/me")
def me(user=Depends(require_role("mother"))):
    return user

@app.get("/api/consultant/ping")#makes the consultants appear under auth in fastAPI
def ping(user=Depends(require_role("consultant"))):
    return{"hello": "consultant"}



