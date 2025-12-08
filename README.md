# RAG-Backend

A Python-based RAG (Retrieval-Augmented Generation) backend that lets you upload PDFs and chat with AI over your documents.

---

## Overview

This project is a simple and practical **RAG backend** built in Python. It allows users to:  

- Upload PDFs and store their content in a vector database (Qdrant).  
- Chat with a powerful LLM (Google Gemini) using the uploaded documents as reference.  
- Maintain chat history with MongoDB-Atlas for user-specific conversations.  

The backend is built using **FastAPI** for easy API access and can be connected to any frontend, including Flutter apps.  

---

## Key Features

- Upload and process PDFs into vector embeddings.  
- Semantic search over documents to provide context-aware answers.  
- Integrates with Gemini LLM for intelligent responses.  
- Chat history storage in MongoDB-Atlas.  
- Logging support to track activity and debug issues.  

---

## Tech Stack

- **Python 3.13+**  
- **FastAPI**  
- **LangChain**  
- **Google Gemini** (LLM + Embeddings)  
- **Qdrant** (Vector Database)  
- **MongoDB Atlas** (Chat history storage)  
- **python-dotenv** for configuration  
- **logging** for monitoring and debugging  

---

## Why This Project?

This is a lightweight, easy-to-understand RAG backend designed for developers who want a practical starting point for building **document-based chatbots or AI assistants**. It’s simple, modular, and ready to deploy to cloud platforms like Railway or Render or Koyeb.

---

## Future Enhancements

- Add authentication for multi-user scenarios.  
- Support multiple document types (Word, PPT).  
- Deploy a frontend interface for easier testing.  
- Add vector database optimization and caching.  

---

## License

This project is open-source and available under the MIT License.  

---

## Acknowledgements

- [LangChain](https://www.langchain.com/) for vector database and LLM integrations  
- [Qdrant](https://qdrant.tech/) for vector storage  
- Google Gemini for LLM and embeddings  
- FastAPI for building a clean backend API  