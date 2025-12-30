from uuid import uuid4
from typing import List
from ..core.logger import logger
from qdrant_client import QdrantClient
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client.http import models as qdrant_models
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..core.config import QDRANT_URL, QDRANT_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP, GEMINI_API_KEY

class VectorStore:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=GEMINI_API_KEY)
        self.qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY) if QDRANT_API_KEY else QdrantClient(url=QDRANT_URL)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        self._user_stores: dict[str, QdrantVectorStore] = {}

    def _get_user_collection_name(self, user_id: str) -> str:
        """Generate a collection name for a specific user."""
        safe_user_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in user_id)
        return f"user_{safe_user_id}_data"

    def _ensure_user_collection_exists(self, user_id: str) -> str:
        """Create user's collection if it doesn't exist. Returns collection name."""
        collection_name = self._get_user_collection_name(user_id)
        

        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            logger.info("Creating new collection for user: %s -> %s", user_id, collection_name)
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=3072,  
                    distance=qdrant_models.Distance.COSINE
                )
            )
        return collection_name

    def _get_user_vector_store(self, user_id: str) -> QdrantVectorStore:
        """Get or create a QdrantVectorStore for a specific user."""
        if user_id not in self._user_stores:
            collection_name = self._ensure_user_collection_exists(user_id)
            self._user_stores[user_id] = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=collection_name,
                embedding=self.embeddings,
            )
        return self._user_stores[user_id]

    def add_documents(self, user_id: str, documents: List[Document]):
        """Split docs into chunks and upsert into user's Qdrant collection."""
        logger.info("Splitting documents into chunks for user: %s", user_id)
        docs = []
        for d in documents:
            chunks = self.text_splitter.split_text(d.page_content)
            for c in chunks:
                docs.append(Document(page_content=c, metadata=d.metadata))
        if not docs:
            return 0
        

        user_store = self._get_user_vector_store(user_id)
        
        ids = [str(uuid4()) for _ in docs]
        logger.info("Upserting %d chunks into Qdrant collection for user: %s", len(docs), user_id)
        user_store.add_documents(
            documents=docs, 
            ids=ids
        )
        return len(docs)

    def retrieve(self, user_id: str, query: str, top_k: int = 3):
        """Return concatenated text from top_k similar docs from user's collection."""

        collection_name = self._get_user_collection_name(user_id)
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            logger.info("No collection found for user: %s", user_id)
            return []
        
        user_store = self._get_user_vector_store(user_id)
        results = user_store.similarity_search_with_score(
            query=query,
            k=top_k,
            score_threshold=0.6
        )
        docs_texts = [{"text": doc.page_content, "metadata": doc.metadata, "score": score} 
                  for doc, score in results]
        return docs_texts
    
    def delete_user_collection(self, user_id: str) -> bool:
        """Delete a user's entire collection. Returns True if deleted, False if not found."""
        collection_name = self._get_user_collection_name(user_id)
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name in collection_names:
            self.qdrant_client.delete_collection(collection_name)

            if user_id in self._user_stores:
                del self._user_stores[user_id]
            logger.info("Deleted collection for user: %s", user_id)
            return True
        return False