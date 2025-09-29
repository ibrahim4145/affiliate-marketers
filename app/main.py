# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users
from app.routes import scraper
from app.routes import industries
from app.routes import queries
import os

app = FastAPI(title="Affiliate Scraper API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://affiliate-marketers.vercel.app").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Affiliate Scraper API running......"}

# Include all routers
app.include_router(users.router, prefix="/api")
app.include_router(industries.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
app.include_router(scraper.router, prefix="/api", tags=["scraper"])
