from typing import Optional
from pydantic import BaseModel

class UploadResponse(BaseModel):
    inserted_chunks: int
    message: str

class ChatRequest(BaseModel):
    user_id: str
    query: str
    top_k: Optional[int] = 3

class ChatResponse(BaseModel):
    answer: str
    source_documents: list