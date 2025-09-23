# # backend/app/routes/contacts.py
# from fastapi import APIRouter
# from app.db import db
# from app.models import Contact

# router = APIRouter()

# @router.get("/contacts")
# async def get_contacts():
#     contacts = await db.contacts.find().to_list(100)
#     for c in contacts:
#         c["_id"] = str(c["_id"])  # convert ObjectId for JSON
#     return contacts

# @router.post("/contacts")
# async def add_contact(contact: Contact):
#     result = await db.contacts.insert_one(contact.dict())
#     return {"inserted_id": str(result.inserted_id)}
