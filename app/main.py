import tempfile
from .logger import logger
from .vector_store import VectorStore
from .chat_service import ChatService
from .pdf_loader import pdf_to_documents
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from .models import UploadResponse, ChatRequest, ChatResponse, DeleteCollectionRequest, DeleteCollectionResponse

app = FastAPI(
    version = "1.0.0",
    title = "RAG System Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = VectorStore()
chatService = ChatService()


@app.get("/")
def health():
    return {"status": "Healthy"}


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User ID to associate the uploaded data with")
):
    """
    Upload a PDF file for a specific user.
    Each user gets their own collection in the vector database.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported.")
    
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id is required.")
    
    user_id = user_id.strip()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    documents = pdf_to_documents(tmp_path)
    inserted = vector_store.add_documents(user_id=user_id, documents=documents)
    collection_name = vector_store._get_user_collection_name(user_id)
    
    logger.info("Inserted %d chunks for user: %s into collection: %s", inserted, user_id, collection_name)
    return UploadResponse(
        user_id=user_id,
        collection_name=collection_name,
        inserted_chunks=inserted,
        message="PDF uploaded and indexed successfully."
    )


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    Chat with the RAG system using documents from the user's specific collection.
    """
    result = chatService.ask(user_id=req.user_id, query=req.query, top_k=req.top_k)
    return ChatResponse(answer=result["answer"], source_documents=result["source_documents"])


@app.delete("/collection", response_model=DeleteCollectionResponse)
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