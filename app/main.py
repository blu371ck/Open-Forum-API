from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import users

app = FastAPI(
    title="Open Forum",
    description="A robust FastAPI backend with user authentication.",
    version="0.1.0",
)

origins = [
    "http://localhost:3000",  # Potential REACT frontends
    "http://localhost:5173",  # Potentiel React/Vue/Vite sitautions
    "http://localhost:8080",  # More specifically for Vue
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/v1", tags=["users"])
