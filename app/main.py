import tempfile
from .logger import logger
from .vector_store import VectorStore
from .chat_service import ChatService
from .pdf_loader import pdf_to_documents
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from .models import UploadResponse, ChatRequest, ChatResponse

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

VectorStore = VectorStore()
chatService = ChatService()

@app.get("/")
def health():
    return {"status": "Healty"}

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), namespace: str = None):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDFs are supported.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    documents = pdf_to_documents(tmp_path)
    inserted = VectorStore.add_documents(documents, namespace=namespace)
    logger.info("Inserted %d chunks", inserted)
    return UploadResponse(inserted_chunks=inserted, message="PDF uploaded and indexed.")

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    result = chatService.ask(user_id=req.user_id, query=req.query, top_k=req.top_k)
    return ChatResponse(answer=result["answer"], source_documents=result["source_documents"])