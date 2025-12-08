import os
from dotenv import load_dotenv

load_dotenv()

# LLM - Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# VectorStore - Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_backend_data")

# Memory - MongoDBAtlas
MONGODB_URL = os.getenv("MONGODB_URL")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "rag_backend_db")
MONGO_CHAT_COLLECTION = os.getenv("MONGO_CHAT_COLLECTION", "chats")

# RAG - Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))