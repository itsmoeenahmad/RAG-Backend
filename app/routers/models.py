from typing import Optional
from pydantic import BaseModel

class UploadRequest(BaseModel):
    user_id: str

class UploadResponse(BaseModel):
    user_id: str
    collection_name: str
    inserted_chunks: int
    message: str

class ChatRequest(BaseModel):
    user_id: str
    query: str
    top_k: Optional[int] = 3

class ChatResponse(BaseModel):
    answer: str
    source_documents: list

class DeleteCollectionRequest(BaseModel):
    user_id: str

class DeleteCollectionResponse(BaseModel):
    user_id: str
    deleted: bool
    message: str