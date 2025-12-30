import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pymongo import MongoClient
from app.core.config import MONGODB_URL

client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
print(client.list_database_names())