from fastapi import FastAPI
from .routers.api import router
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(router)