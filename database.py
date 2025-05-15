import os
import logging
from typing import List, Optional
from dotenv import load_dotenv
import pymongo
from pymongo.errors import ServerSelectionTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError("❌ MongoDB URL এনভায়রনমেন্ট ভেরিয়েবলে সেট করা নেই!")

try:
    client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    logger.info("✅ MongoDB-তে সফলভাবে কানেক্ট হয়েছে!")
except ServerSelectionTimeoutError as e:
    logger.error("❌ MongoDB-তে কানেক্ট হতে ব্যর্থ: %s", e)
    raise

db = client["telegram_bot"]
users_collection = db["users"]
users_collection.create_index("user_id", unique=True)  # Optimize queries

def add_user(user_id: int, username: str) -> None:
    """Add/update a user in the database."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"username": username, "approved": False}},
        upsert=True
    )
    logger.info(f"User {user_id} added/updated in DB")

def approve_user(user_id: int) -> None:
    """Approve a user."""
    users_collection.update_one(
        {"user_id": user_id}, 
        {"$set": {"approved": True}}
    )
    logger.info(f"User {user_id} approved")

def is_approved(user_id: int) -> bool:
    """Check if a user is approved."""
    user = users_collection.find_one({"user_id": user_id})
    return user and user.get("approved", False)

def get_all_users() -> List[int]:
    """Get all approved user IDs."""
    return [user["user_id"] for user in users_collection.find({"approved": True})]
