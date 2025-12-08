from .logger import logger
from .config import GEMINI_API_KEY
from .vector_store import VectorStore
from .db_service import save_message, get_chat_history
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ChatService:
    def __init__(self):
        self.vectorStore = VectorStore()
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.2)

    def ask(self, user_id: str, query: str, top_k: int = 3):
        # retrieve docs from VectoreStore
        logger.info("Searching vectorstore for relevant docs...")
        retrieved = self.vectorStore.retrieve(query, top_k=top_k)
        reference_text = "\n\n".join([r["text"] for r in retrieved]) if retrieved else ""
        # fetch chat history to provide context (simple format)
        history = get_chat_history(user_id)
        messages = [
            SystemMessage(content="You are a concise helpful assistant. Use reference data to answer user. If insufficient, say you don't have enough info.")
        ]
        # append history (human/assistant) as Messages
        for h in history:
            messages.append(HumanMessage(content=h["human"]))
            messages.append(AIMessage(content=h["assistant"]))
        # current user question + reference data
        messages.append(HumanMessage(content=f"User Question: {query}\n\nReference Data:\n{reference_text}"))
        # call llm
        logger.info("Calling Gemini LLM...")
        response = self.llm.invoke(messages).content
        # save to mongo
        save_message(user_id=user_id, human=query, assistant=response)
        return {"answer": response, "source_documents": retrieved}