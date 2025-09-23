# backend/app/main.py
from fastapi import FastAPI
from app.routes import contacts
from app.routes import users
from app.routes import scraper
# from app.scheduler import init_scheduler

app = FastAPI(title="Affiliate Scraper API")

# include routes
# app.include_router(contacts.router, prefix="/api", tags=["contacts"])

# @app.on_event("startup")
# async def startup_event():
#     init_scheduler()

@app.get("/")
def root():
    return {"message": "Affiliate Scraper API running 🚀"}

app.include_router(users.router)
app.include_router(scraper.router, prefix="/api", tags=["scraper"])
