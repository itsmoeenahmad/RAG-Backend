import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from qdrant_client import QdrantClient
from qdrant_client.http import models as m
from app.config import QDRANT_URL, QDRANT_COLLECTION, QDRANT_API_KEY

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY) if QDRANT_API_KEY else QdrantClient(url=QDRANT_URL)
client.create_collection(
    collection_name=QDRANT_COLLECTION,
    vectors_config=m.VectorParams(size=3072, distance=m.Distance.COSINE)
)
print("Created collection:", QDRANT_COLLECTION)