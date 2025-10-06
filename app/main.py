# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, industries, queries, leads, email, phone, social, scraper, sub_queries
from app.models.user import user_model
from app.models.industry import industry_model
from app.models.query import query_model
from app.models.lead import lead_model
from app.models.email import email_model
from app.models.phone import phone_model
from app.models.social import social_model
from app.models.scraper import scraper_progress_model
from app.models.sub_query import sub_query_model

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
app.include_router(leads.router, prefix="/api")
app.include_router(email.router, prefix="/api")
app.include_router(phone.router, prefix="/api")
app.include_router(social.router, prefix="/api")
app.include_router(scraper.router, prefix="/api")
app.include_router(sub_queries.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Create all necessary indexes on startup."""
    try:
        await user_model.create_indexes()
        await industry_model.create_indexes()
        await query_model.create_indexes()
        await lead_model.create_indexes()
        await email_model.create_indexes()
        await phone_model.create_indexes()
        await social_model.create_indexes()
        await scraper_progress_model.create_indexes()
        await sub_query_model.create_indexes()
        print("✅ All database indexes created successfully")
    except Exception as e:
        print(f"❌ Error creating indexes: {str(e)}")