# RAG-Backend

A production-ready Python RAG (Retrieval-Augmented Generation) backend with **async document processing** to prevent edge timeout errors on serverless platforms like Koyeb. Features per-user data isolation with job tracking and progress monitoring.

> **🚀 NEW**: Async upload processing eliminates 502/504 timeout errors for large documents. See [DEPLOYMENT_FIX.md](DEPLOYMENT_FIX.md) for details.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Future Enhancements](#future-enhancements)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

This project is a **production-grade RAG backend** built in Python with FastAPI. It allows users to:

- Upload PDFs with **async processing** (no edge timeouts)
- Store content in **user-specific** vector collections (Qdrant)
- Track upload progress with job status polling
- Chat with Google Gemini LLM using only their own documents
- Maintain chat history in MongoDB Atlas

The backend is optimized for **serverless deployment** (Koyeb, Cloud Run, Lambda) and handles large documents (1000+ pages) without timeout issues.

### How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   User A    │────▶│   FastAPI   │────▶│  Background Task    │
│  Upload PDF │     │ (Returns    │     │  - Extract text     │
└─────────────┘     │  job_id)    │     │  - Generate embeds  │
                    └─────────────┘     │  - Batch upsert     │
                           │            └─────────────────────┘
                           │                      │
                           ▼                      ▼
                    ┌─────────────┐     ┌─────────────────────┐
                    │ Poll Status │     │  user_A_data        │
                    │  Endpoint   │     │  (Qdrant Collection)│
                    └─────────────┘     └─────────────────────┘
```

Each user's documents are isolated in their own collection with **job-based async processing** to eliminate edge proxy timeouts.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Async Upload Processing** | Returns job_id immediately, processes in background (no timeouts) |
| **Job Status Tracking** | Poll `/upload/status/{job_id}` for progress updates (0-100%) |
| **Per-User Data Isolation** | Each user gets their own Qdrant collection (\`user_<id>_data\`) |
| **Batched Qdrant Upserts** | 100 chunks per batch for reliability and memory efficiency |
| **PDF Processing** | Upload and process large PDFs (1000+ pages) without issues |
| **Semantic Search** | Find relevant document chunks based on query meaning |
| **AI-Powered Chat** | Integrates with Google Gemini for intelligent responses |
| **Chat History** | Conversation history stored in MongoDB Atlas |
| **Collection Management** | Delete user's entire collection when needed |
| **Production Ready** | Handles edge timeouts, rate limits, and error recovery |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  PDF Loader │  │ VectorStore │  │     Chat Service        │  │
│  │  (pypdf)    │  │  (Qdrant)   │  │  (Gemini + LangChain)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                        External Services                         │
├──────────────┬────────────────────┬─────────────────────────────┤
│  Qdrant      │  MongoDB Atlas     │  Google Gemini API          │
│  (Vectors)   │  (Chat History)    │  (LLM + Embeddings)         │
└──────────────┴────────────────────┴─────────────────────────────┘
```

---

## Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.13+ |
| **Framework** | FastAPI |
| **LLM** | Google Gemini 2.5 Flash |
| **Embeddings** | Gemini Embedding 001 (3072 dimensions) |
| **Vector DB** | Qdrant Cloud |
| **Database** | MongoDB Atlas |
| **Orchestration** | LangChain |
| **PDF Processing** | pypdf |

---

## Project Structure

```
rag-backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── core/                # Core utilities
│   │   ├── config.py        # Environment configuration
│   │   └── logger.py        # Logging setup
│   ├── routers/             # API route definitions
│   │   ├── api.py           # All endpoints
│   │   └── models.py        # Pydantic request/response models
│   ├── services/            # Business logic and integrations
│   │   ├── chat_service.py  # LLM chat with RAG
│   │   ├── db_service.py    # MongoDB chat history
│   │   └── vector_store.py  # Qdrant vector operations (per-user)
│   └── loaders/             # Data loading utilities
│       └── pdf_loader.py    # PDF text extraction
├── tests/
│   └── test.py              # Test scripts
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment file
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── pyproject.toml           # Python project configuration
└── README.md                # This file
```

---

## Installation

### Prerequisites

- Python 3.13 or higher
- Qdrant Cloud account (or local Qdrant instance)
- MongoDB Atlas account
- Google Gemini API key

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rag-backend.git
   cd rag-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (see [Configuration](#configuration))

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## Configuration

Create a \`.env\` file in the root directory:

```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Qdrant Vector Database
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here

# MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?appName=YourApp
MONGO_DB_NAME=rag_backend_db
MONGO_CHAT_COLLECTION=chats

# RAG Settings
CHUNK_SIZE=800
CHUNK_OVERLAP=100
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| \`GEMINI_API_KEY\` | Google Gemini API key | Required |
| \`QDRANT_URL\` | Qdrant instance URL | Required |
| \`QDRANT_API_KEY\` | Qdrant API key | Optional (for cloud) |
| \`MONGODB_URL\` | MongoDB connection string | Required |
| \`MONGO_DB_NAME\` | MongoDB database name | \`rag_backend_db\` |
| \`MONGO_CHAT_COLLECTION\` | Collection for chat history | \`chats\` |
| \`CHUNK_SIZE\` | Text chunk size for splitting | \`800\` |
| \`CHUNK_OVERLAP\` | Overlap between chunks | \`100\` |

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Health Check
```http
GET /
```

**Response:**
```json
{
  "status": "🚀 RAG Backend Online",
  "message": "Ready to ingest documents and answer questions!",
  "version": "2.0.0",
  "timestamp": "2026-01-31T12:34:56.789Z",
  "features": {
    "async_upload": true,
    "job_tracking": true,
    "batched_processing": true,
    "per_user_isolation": true
  },
  "endpoints": {
    "upload": "POST /upload - Upload PDF for async processing",
    "status": "GET /upload/status/{job_id} - Check upload progress",
    "chat": "POST /chat - Query your documents with AI",
    "delete": "DELETE /collection - Remove user collection"
  },
  "powered_by": ["FastAPI", "Qdrant", "Google Gemini", "MongoDB"]
}
```

**Description:**
- **status**: Current system status with emoji
- **message**: Human-friendly welcome message
- **version**: API version (2.0.0 includes async upload features)
- **timestamp**: Current server time in ISO 8601 format
- **features**: Boolean flags for available features
- **endpoints**: Quick reference for all API endpoints
- **powered_by**: Technology stack

---

#### Upload PDF (Async)
```http
POST /upload
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| \`file\` | File | form-data | Yes | PDF file to upload |
| \`user_id\` | string | form-data | Yes | Unique user identifier |

**Response** (returns immediately):
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user123",
  "status": "queued",
  "message": "Upload queued successfully. Use GET /upload/status/{job_id} to check progress.",
  "created_at": "2026-01-31T12:00:00.123Z"
}
```

**Status Code**: `200 OK` (instant response, typically < 500ms)

---

#### Check Upload Status
```http
GET /upload/status/{job_id}
```

**Path Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| \`job_id\` | string | Yes | Job ID returned from `/upload` |

**Response Examples:**

**Queued:**
```json
{
  "job_id": "a1b2c3d4-...",
  "user_id": "user123",
  "status": "queued",
  "filename": "document.pdf",
  "progress_percent": 0,
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:00:00Z"
}
```

**Processing:**
```json
{
  "job_id": "a1b2c3d4-...",
  "user_id": "user123",
  "status": "processing",
  "filename": "document.pdf",
  "progress_percent": 60,
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:01:30Z"
}
```

**Completed:**
```json
{
  "job_id": "a1b2c3d4-...",
  "user_id": "user123",
  "status": "completed",
  "filename": "document.pdf",
  "collection_name": "user_user123_data",
  "inserted_chunks": 2255,
  "progress_percent": 100,
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:03:45Z"
}
```

**Failed:**
```json
{
  "job_id": "a1b2c3d4-...",
  "user_id": "user123",
  "status": "failed",
  "error_message": "Failed to connect to Qdrant",
  "progress_percent": 30,
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:02:15Z"
}
```

**Status Values:**
- `queued`: Job created, waiting to start
- `processing`: Currently extracting text and generating embeddings
- `completed`: Successfully ingested into Qdrant
- `failed`: Error occurred (check `error_message`)

---

#### Chat
```http
POST /chat
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "user123",
  "query": "What is the main topic of my document?",
  "top_k": 3
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| \`user_id\` | string | Yes | - | User identifier |
| \`query\` | string | Yes | - | Question to ask |
| \`top_k\` | integer | No | 3 | Number of relevant chunks to retrieve |

**Response:**
```json
{
  "answer": "Based on your documents, the main topic is...",
  "source_documents": [
    {
      "text": "Relevant chunk of text...",
      "metadata": {"source": "/path/to/file.pdf"},
      "score": 0.85
    }
  ]
}
```

---

#### Delete User Collection
```http
DELETE /collection
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "user123"
}
```

**Response:**
```json
{
  "user_id": "user123",
  "deleted": true,
  "message": "Collection deleted successfully."
}
```

---

## Usage Examples

### Using cURL

**Upload a PDF (async):**
```bash
# Step 1: Upload and get job_id
curl -X POST "http://localhost:8000/upload" \
  -F "file=@large_document.pdf" \
  -F "user_id=user123"

# Response:
# {
#   "job_id": "abc-123-...",
#   "status": "queued",
#   "message": "Upload queued successfully..."
# }

# Step 2: Check status (poll every 3-5 seconds)
curl "http://localhost:8000/upload/status/abc-123-..."

# Response shows progress:
# {
#   "status": "processing",
#   "progress_percent": 60,
#   ...
# }
```

**Chat with your documents:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "query": "Summarize the key points from my document",
    "top_k": 5
  }'
```

**Delete user collection:**
```bash
curl -X DELETE "http://localhost:8000/collection" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

### Using Python

```python
import time
import requests

BASE_URL = "http://localhost:8000"
USER_ID = "user123"

# Upload PDF (async)
with open("document.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f},
        data={"user_id": USER_ID}
    )

job = response.json()
job_id = job['job_id']
print(f"Job queued: {job_id}")

# Poll for completion
while True:
    status_response = requests.get(f"{BASE_URL}/upload/status/{job_id}")
    status = status_response.json()
    
    print(f"Progress: {status['progress_percent']}% - {status['status']}")
    
    if status['status'] == 'completed':
        print(f"✓ Uploaded: {status['inserted_chunks']} chunks")
        break
    elif status['status'] == 'failed':
        print(f"✗ Failed: {status['error_message']}")
        break
    
    time.sleep(3)  # Poll every 3 seconds

# Chat
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "user_id": USER_ID,
        "query": "What are the main findings?",
        "top_k": 3
    }
)
print(response.json()["answer"])
```

### Using JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";
const USER_ID = "user123";

// Upload PDF (async with polling)
async function uploadPDF(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", USER_ID);

  // Step 1: Upload
  const uploadResponse = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData
  });
  
  const { job_id } = await uploadResponse.json();
  console.log('Job queued:', job_id);
  
  // Step 2: Poll for status
  return new Promise((resolve, reject) => {
    const pollInterval = setInterval(async () => {
      const statusRes = await fetch(`${BASE_URL}/upload/status/${job_id}`);
      const status = await statusRes.json();
      
      console.log(`${status.progress_percent}% - ${status.status}`);
      
      if (status.status === 'completed') {
        clearInterval(pollInterval);
        resolve(status);
      } else if (status.status === 'failed') {
        clearInterval(pollInterval);
        reject(new Error(status.error_message));
      }
    }, 3000); // Poll every 3 seconds
  });
}

// Usage
try {
  const result = await uploadPDF(pdfFile);
  console.log(`✓ Uploaded: ${result.inserted_chunks} chunks`);
} catch (error) {
  console.error('✗ Upload failed:', error);
}

// Chat
const chatResponse = await fetch(`${BASE_URL}/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: USER_ID,
    query: "Explain the introduction section",
    top_k: 3
  })
});
const result = await chatResponse.json();
console.log(result.answer);
```

---

## Production Deployment

### Koyeb / Serverless Platforms

This backend is optimized for serverless deployment with **async job processing** to prevent edge timeout issues.

**Key Features for Production:**
- ✅ Immediate HTTP responses (< 500ms)
- ✅ Background processing for long tasks
- ✅ Job status tracking via polling
- ✅ Batched Qdrant upserts (100 chunks/batch)
- ✅ Automatic error recovery and logging

**Deployment Steps:**

1. **Set environment variables** in your platform dashboard:
   ```env
   GEMINI_API_KEY=your_key
   QDRANT_URL=https://...
   QDRANT_API_KEY=your_key
   MONGODB_URL=mongodb+srv://...
   CHUNK_SIZE=800
   CHUNK_OVERLAP=100
   ```

2. **Deploy from GitHub** (automatic detection of FastAPI app)

3. **Test with a large document** to verify no 502/504 errors

4. **Monitor logs** for job processing status

**Important:** See [DEPLOYMENT_FIX.md](DEPLOYMENT_FIX.md) for detailed explanation of the async upload architecture and [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing procedures.

---

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t rag-backend .

# Run the container
docker run -d \
  --name rag-backend \
  -p 8000:8000 \
  --env-file .env \
  rag-backend
```

### Docker Compose (optional)

Create a \`docker-compose.yml\`:

```yaml
version: '3.8'
services:
  rag-backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

---

## Future Enhancements

- [ ] Add JWT authentication for secure multi-user access
- [ ] Support multiple document types (Word, PPT, TXT)
- [ ] Add streaming responses for chat
- [ ] Implement rate limiting
- [ ] Add document metadata management
- [ ] Create admin dashboard for collection management
- [ ] Add support for image extraction from PDFs
- [ ] Implement caching for frequently accessed documents

---

## License

This project is open-source and available under the MIT License.

---

## Acknowledgements

- [LangChain](https://www.langchain.com/) for vector database and LLM integrations
- [Qdrant](https://qdrant.tech/) for vector storage
- [Google Gemini](https://ai.google.dev/) for LLM and embeddings
- [FastAPI](https://fastapi.tiangolo.com/) for building a clean backend API
- [MongoDB Atlas](https://www.mongodb.com/atlas) for chat history storage

---

## Support

If you encounter any issues or have questions, please open an issue on GitHub.