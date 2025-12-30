from datetime import datetime
from ..core.logger import logger
from pymongo import MongoClient, ASCENDING
from ..core.config import MONGODB_URL, MONGO_DB_NAME, MONGO_CHAT_COLLECTION

client = MongoClient(MONGODB_URL)
db = client[MONGO_DB_NAME]
chat_collection = db[MONGO_CHAT_COLLECTION]

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