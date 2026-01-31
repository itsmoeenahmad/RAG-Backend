# app/routers/api.py
import os
import tempfile
from uuid import uuid4
from ..core.logger import logger
from ..services.vector_store import VectorStore
from ..services.chat_service import ChatService
from ..loaders.pdf_loader import pdf_to_documents
from ..services.db_service import create_upload_job, update_job_status, get_job_status
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from .models import (
    UploadJobResponse, JobStatusResponse, ChatRequest, ChatResponse, 
    DeleteCollectionRequest, DeleteCollectionResponse
)

router = APIRouter()

vector_store = VectorStore()
chat_service = ChatService()

@router.get("/")
def health():
    """
    Health check endpoint with system information.
    Returns server status, version, and available endpoints.
    """
    from datetime import datetime
    return {
        "status": "🚀 RAG Backend Online",
        "message": "Ready to ingest documents and answer questions!",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "features": {
            "async_upload": True,
            "job_tracking": True,
            "batched_processing": True,
            "per_user_isolation": True
        },
        "endpoints": {
            "upload": "POST /upload - Upload PDF for async processing",
            "status": "GET /upload/status/{job_id} - Check upload progress",
            "chat": "POST /chat - Query your documents with AI",
            "delete": "DELETE /collection - Remove user collection"
        },
        "powered_by": ["FastAPI", "Qdrant", "Google Gemini", "MongoDB"]
    }


# Background processing function
def process_pdf_upload(job_id: str, user_id: str, file_path: str, filename: str):
    """
    Background task to process PDF upload.
    Handles document splitting, embedding generation, and Qdrant ingestion.
    """
    try:
        logger.info("Starting background processing for job: %s", job_id)
        update_job_status(job_id, "processing", progress_percent=10)
        
        # Extract text from PDF
        logger.info("Extracting text from PDF: %s", filename)
        documents = pdf_to_documents(file_path)
        update_job_status(job_id, "processing", progress_percent=30)
        
        # Add documents with batched processing (100 chunks per batch)
        logger.info("Adding documents to vector store for user: %s", user_id)
        inserted = vector_store.add_documents(user_id=user_id, documents=documents, batch_size=100)
        update_job_status(job_id, "processing", progress_percent=90)
        
        # Get collection name
        collection_name = vector_store._get_user_collection_name(user_id)
        
        # Mark as completed
        update_job_status(
            job_id=job_id,
            status="completed",
            collection_name=collection_name,
            inserted_chunks=inserted,
            progress_percent=100
        )
        
        logger.info("Job %s completed: %d chunks inserted for user: %s", job_id, inserted, user_id)
        
    except Exception as e:
        logger.error("Job %s failed: %s", job_id, str(e), exc_info=True)
        update_job_status(
            job_id=job_id,
            status="failed",
            error_message=str(e)
        )
    finally:
        # Cleanup temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Cleaned up temp file: %s", file_path)
        except Exception as cleanup_error:
            logger.warning("Failed to cleanup temp file %s: %s", file_path, cleanup_error)


@router.post("/upload", response_model=UploadJobResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User ID to associate the uploaded data with")
):
    """
    Upload a PDF file for async processing.
    Returns immediately with job_id. Use /upload/status/{job_id} to check progress.
    
    Prevents edge proxy timeouts by processing in background.
    """
    # Validation
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported.")
    
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")
    
    user_id = user_id.strip()
    
    # Generate unique job ID
    job_id = str(uuid4())
    
    # Save file to temp location (persistent across background task)
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    # Create job record
    create_upload_job(job_id=job_id, user_id=user_id, filename=file.filename)
    
    # Schedule background processing
    background_tasks.add_task(
        process_pdf_upload,
        job_id=job_id,
        user_id=user_id,
        file_path=temp_file.name,
        filename=file.filename
    )
    
    logger.info("Upload job %s queued for user: %s, file: %s", job_id, user_id, file.filename)
    
    # Return immediately
    from datetime import datetime
    return UploadJobResponse(
        job_id=job_id,
        user_id=user_id,
        status="queued",
        message=f"Upload queued successfully. Use GET /upload/status/{job_id} to check progress.",
        created_at=datetime.utcnow()
    )


@router.get("/upload/status/{job_id}", response_model=JobStatusResponse)
def get_upload_status(job_id: str):
    """
    Check the status of an upload job.
    
    Status values:
    - queued: Job created, waiting to start
    - processing: Currently processing document
    - completed: Successfully ingested into Qdrant
    - failed: Error occurred (check error_message)
    """
    job = get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatusResponse(**job)

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    Chat with the RAG system using documents from the user's specific collection.
    """
    result = chat_service.ask(user_id=req.user_id, query=req.query, top_k=req.top_k)
    return ChatResponse(answer=result["answer"], source_documents=result["source_documents"])

@router.delete("/collection", response_model=DeleteCollectionResponse)
def delete_user_collection(req: DeleteCollectionRequest):
    """
    Delete a user's entire vector collection.
    Use with caution - this removes all uploaded documents for the user.
    """
    deleted = vector_store.delete_user_collection(user_id=req.user_id)
    if deleted:
        return DeleteCollectionResponse(
            user_id=req.user_id,
            deleted=True,
            message="Collection deleted successfully."
        )
    return DeleteCollectionResponse(
        user_id=req.user_id,
        deleted=False,
        message="No collection found for this user."
    )