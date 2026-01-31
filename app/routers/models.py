from typing import Optional, Literal
from pydantic import BaseModel
from datetime import datetime

class UploadRequest(BaseModel):
    user_id: str

# New async response model
class UploadJobResponse(BaseModel):
    job_id: str
    user_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    message: str
    created_at: datetime

# Legacy sync response (kept for backward compatibility)
class UploadResponse(BaseModel):
    user_id: str
    collection_name: str
    inserted_chunks: int
    message: str

# Job status response
class JobStatusResponse(BaseModel):
    job_id: str
    user_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    filename: Optional[str] = None
    collection_name: Optional[str] = None
    inserted_chunks: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    progress_percent: Optional[int] = None

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