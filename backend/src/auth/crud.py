from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

async def get_user_by_email(email: str):
    """Get user by email from MongoDB or in-memory storage"""
    db = get_database()
    
    if db.mongodb_connected:
        try:
            user = await db.users_collection.find_one({"email": email})
            return user
        except Exception as e:
            logger.error(f"Error querying MongoDB: {e}")
            # Fall back to in-memory storage
            pass

async def authenticate_user(email: str, password: str):
    """Authenticate user by email and password"""
    user = await get_user_by_email(email)
    if not user:
        return False
    
    if not verify_password(password, user["hashed_password"]):
        return False
    
    return user

async def update_user_profile(email: str, name: str):
    """Update user profile information"""
    db = get_database()
    
    if db.mongodb_connected:
        try:
            # Update in MongoDB
            result = await db.users_collection.update_one(
                {"email": email},
                {"$set": {"name": name}}
            )
            if result.modified_count > 0:
                # Return updated user
                updated_user = await db.users_collection.find_one({"email": email})
                logger.info(f"User {email} profile updated in MongoDB")
                return updated_user
        except Exception as e:
            logger.error(f"Error updating user profile in MongoDB: {e}")
            # Fall back to in-memory storage
            pass
    
    # In-memory storage fallback
    for user_id, user in db.in_memory_users.items():
        if user["email"] == email:
            user["name"] = name
            logger.info(f"User {email} profile updated in memory storage")
            return user
    
    return None