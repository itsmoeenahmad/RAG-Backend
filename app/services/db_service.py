from datetime import datetime
from typing import Optional
from ..core.logger import logger
from pymongo import MongoClient, ASCENDING
from ..core.config import MONGODB_URL, MONGO_DB_NAME, MONGO_CHAT_COLLECTION

client = MongoClient(MONGODB_URL)
db = client[MONGO_DB_NAME]
chat_collection = db[MONGO_CHAT_COLLECTION]
jobs_collection = db["upload_jobs"]

def save_message(user_id: str, human: str, assistant: str):
    item = {
        "user_id": user_id,
        "human": human,
        "assistant": assistant,
        "timestamp": datetime.utcnow()
    }
    chat_collection.insert_one(item)
    logger.info("Saved chat message for user: %s", user_id)

def get_chat_history(user_id: str, limit: int = 20):
    cursor = list(chat_collection.find({"user_id": user_id}).sort("timestamp", ASCENDING).limit(limit))
    history = []
    for it in cursor:
        history.append({"human": it["human"], "assistant": it["assistant"]})
    return history

# Upload job tracking
def create_upload_job(job_id: str, user_id: str, filename: str):
    """Create a new upload job entry."""
    job = {
        "job_id": job_id,
        "user_id": user_id,
        "filename": filename,
        "status": "queued",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "progress_percent": 0
    }
    jobs_collection.insert_one(job)
    logger.info("Created upload job: %s for user: %s", job_id, user_id)
    return job

def update_job_status(
    job_id: str,
    status: str,
    collection_name: Optional[str] = None,
    inserted_chunks: Optional[int] = None,
    error_message: Optional[str] = None,
    progress_percent: Optional[int] = None
):
    """Update job status and metadata."""
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    if collection_name:
        update_data["collection_name"] = collection_name
    if inserted_chunks is not None:
        update_data["inserted_chunks"] = inserted_chunks
    if error_message:
        update_data["error_message"] = error_message
    if progress_percent is not None:
        update_data["progress_percent"] = progress_percent
    
    jobs_collection.update_one(
        {"job_id": job_id},
        {"$set": update_data}
    )
    logger.info("Updated job %s: status=%s", job_id, status)

def get_job_status(job_id: str):
    """Get current job status."""
    job = jobs_collection.find_one({"job_id": job_id})
    if job:
        job.pop("_id", None)  # Remove MongoDB internal ID
    return job