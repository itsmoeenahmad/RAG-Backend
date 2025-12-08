from uuid import uuid4
from typing import List
from .logger import logger
from qdrant_client import QdrantClient
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, CHUNK_SIZE, CHUNK_OVERLAP, GEMINI_API_KEY

class VectorStore:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=GEMINI_API_KEY)
        self.qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY) if QDRANT_API_KEY else QdrantClient(url=QDRANT_URL)
        self.vectorStore = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=QDRANT_COLLECTION,
            embedding=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    def add_documents(self, documents: List[Document], namespace: str = None):
        """Split docs into chunks and upsert into Qdrant."""
        logger.info("Splitting documents into chunks...")
        docs = []
        for d in documents:
            chunks = self.text_splitter.split_text(d.page_content)
            for c in chunks:
                docs.append(Document(page_content=c, metadata=d.metadata))
        if not docs:
            return 0
        ids = [str(uuid4()) for _ in docs]
        logger.info("Upserting %d chunks into Qdrant...", len(docs))
        self.vectorStore.add_documents(
            documents=docs, 
            ids=ids
        )
        return len(docs)

    def retrieve(self, query: str, top_k: int = 3):
        """Return concatenated text from top_k similar docs"""
        results = self.vectorStore.similarity_search_with_score(
            query=query,
            k=top_k,
            score_threshold=0.6
        )
        docs_texts = [{"text": doc.page_content, "metadata": doc.metadata, "score": score} 
                  for doc, score in results]
        return docs_texts