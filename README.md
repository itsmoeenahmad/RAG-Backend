# RAG-Backend

A Python-based RAG (Retrieval-Augmented Generation) backend that lets you upload PDFs and chat with AI over your documents. Features **per-user data isolation** where each user gets their own vector collection.

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
- [Future Enhancements](#future-enhancements)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

This project is a simple and practical **RAG backend** built in Python. It allows users to:

- Upload PDFs and store their content in a **user-specific** vector database collection (Qdrant).
- Chat with a powerful LLM (Google Gemini) using only the user's own uploaded documents as reference.
- Maintain chat history with MongoDB Atlas for user-specific conversations.

The backend is built using **FastAPI** for easy API access and can be connected to any frontend, including Flutter apps, React, or mobile applications.

### How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   User A    │────▶│   FastAPI   │────▶│  user_A_data        │
│  Upload PDF │     │   Backend   │     │  (Qdrant Collection)│
└─────────────┘     └─────────────┘     └─────────────────────┘
                           │
┌─────────────┐            │            ┌─────────────────────┐
│   User B    │────────────┘───────────▶│  user_B_data        │
│  Upload PDF │                         │  (Qdrant Collection)│
└─────────────┘                         └─────────────────────┘
```

Each user's documents are stored in their own isolated collection, ensuring **complete data privacy**.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Per-User Data Isolation** | Each user gets their own Qdrant collection (\`user_<id>_data\`) |
| **PDF Processing** | Upload and process PDFs into vector embeddings |
| **Semantic Search** | Find relevant document chunks based on query meaning |
| **AI-Powered Chat** | Integrates with Google Gemini for intelligent responses |
| **Chat History** | Conversation history stored in MongoDB Atlas |
| **Collection Management** | Delete user's entire collection when needed |
| **Comprehensive Logging** | Track activity and debug issues easily |

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
  "status": "Healthy"
}
```

---

#### Upload PDF
```http
POST /upload
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Location | Required | Description |
|------|------|----------|----------|-------------|
| \`file\` | File | form-data | Yes | PDF file to upload |
| \`user_id\` | string | form-data | Yes | Unique user identifier |

**Response:**
```json
{
  "user_id": "user123",
  "collection_name": "user_user123_data",
  "inserted_chunks": 42,
  "message": "PDF uploaded and indexed successfully."
}
```

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

**Upload a PDF:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf" \
  -F "user_id=user123"
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
import requests

BASE_URL = "http://localhost:8000"
USER_ID = "user123"

# Upload PDF
with open("document.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f},
        data={"user_id": USER_ID}
    )
print(response.json())

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

// Upload PDF
const formData = new FormData();
formData.append("file", pdfFile);
formData.append("user_id", USER_ID);

const uploadResponse = await fetch(\`\${BASE_URL}/upload\`, {
  method: "POST",
  body: formData
});

// Chat
const chatResponse = await fetch(\`\${BASE_URL}/chat\`, {
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