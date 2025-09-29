# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import users
from app.routes import scraper
from app.routes import industries
from app.routes import queries
import os

app = FastAPI(title="Affiliate Scraper API")

# CORS configuration
allowed_origins = [
    "http://localhost:3000",
    "https://affiliate-marketers.vercel.app",
    "https://affiliate-marketers.vercel.app/",
    "https://*.vercel.app"
]

# Add environment variable origins if they exist
env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if env_origins and env_origins[0]:
    allowed_origins.extend(env_origins)

print(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Affiliate Scraper API running......"}

@app.get("/cors-test")
def cors_test():
    return {"message": "CORS test endpoint", "allowed_origins": allowed_origins}

# Include all routers
app.include_router(users.router, prefix="/api")
app.include_router(industries.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
app.include_router(scraper.router, prefix="/api", tags=["scraper"])
