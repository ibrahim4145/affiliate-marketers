# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import contacts
from app.routes import users
from app.routes import scraper
from app.routes import industries
from app.routes import queries
# from app.scheduler import init_scheduler

app = FastAPI(title="Affiliate Scraper API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routes
# app.include_router(contacts.router, prefix="/api", tags=["contacts"])

# @app.on_event("startup")
# async def startup_event():
#     init_scheduler()

@app.get("/")
def root():
    return {"message": "Affiliate Scraper API running 🚀"}

# Include all routers
app.include_router(users.router, prefix="/api")
app.include_router(scraper.router, prefix="/api", tags=["scraper"])
