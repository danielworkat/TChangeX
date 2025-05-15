# database.py

import os
from dotenv import load_dotenv
import pymongo


load_dotenv() # ✅
# Load MongoDB URL from environment variables
MONGO_URL = os.getenv("MONGO_URL")

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URL)
db = client["telegram_bot"]
users_collection = db["users"]

def add_user(user_id, username):
    """Add a user to the database."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "approved": False}},
        upsert=True
    )

def approve_user(user_id):
    """Approve a user."""
    users_collection.update_one({"user_id": user_id}, {"$set": {"approved": True}})

def is_approved(user_id):
    """Check if a user is approved."""
    user = users_collection.find_one({"user_id": user_id})
    return user and user.get("approved", False)

def get_all_users():
    """Get all approved users."""
    return [user["user_id"] for user in users_collection.find({"approved": True})]
