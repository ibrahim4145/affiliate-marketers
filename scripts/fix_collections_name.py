from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB")

def fix_collection_names():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    collections = db.list_collection_names()
    print("Available collections:", collections)

    for name in collections:
        new_name = name.strip()  # remove leading/trailing spaces
        if new_name != name:
            print(f"Renaming '{name}' → '{new_name}' ...")
            db[name].rename(new_name)
        else:
            print(f"Skipping '{name}', no trailing spaces.")

    print("\nDone! Updated collection names:")
    print(db.list_collection_names())

if __name__ == "__main__":
    fix_collection_names()
