# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users
from app.routes import scraper
from app.routes import industries
from app.routes import queries
from app.routes import leads
import os

app = FastAPI(title="Affiliate Scraper API")

# CORS configuration - Allow all origins for now to fix the issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Affiliate Scraper API running......"}

@app.get("/cors-test")
def cors_test():
    return {"message": "CORS test endpoint", "allowed_origins": ["*"]}

# Include all routers
app.include_router(users.router, prefix="/api")
app.include_router(industries.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
app.include_router(leads.router, prefix="/api", tags=["leads"])
app.include_router(scraper.router, prefix="/api", tags=["scraper"])
