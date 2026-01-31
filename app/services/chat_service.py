from ..core.logger import logger
from ..core.config import GEMINI_API_KEY
from .vector_store import VectorStore
from .db_service import save_message, get_chat_history
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ChatService:
    def __init__(self):
        self.vectorStore = VectorStore()
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.2)

    def ask(self, user_id: str, query: str, top_k: int = 3):
        logger.info("Searching vectorstore for relevant docs for user: %s", user_id)
        retrieved = self.vectorStore.retrieve(user_id=user_id, query=query, top_k=top_k)
        reference_text = "\n\n".join([r["text"] for r in retrieved]) if retrieved else ""

        history = get_chat_history(user_id)
        messages = [
            SystemMessage(content="""You are an intelligent and thorough assistant with access to the user's document collection.

CRITICAL INSTRUCTIONS:
1. ALWAYS read and analyze the Reference Data provided below FIRST before responding
2. Base your response primarily on the retrieved document content
3. Provide DETAILED and COMPREHENSIVE answers using the information from the documents
4. Structure your response clearly with proper explanations
5. If the Reference Data contains relevant information, explain it thoroughly - don't be overly brief
6. You may supplement with additional context or clarification ONLY if it:
   - Directly supports and aligns with the document content
   - Helps explain or contextualize the retrieved information
   - Is factually accurate and current (not outdated information)
7. If the Reference Data is insufficient or irrelevant to answer the question, clearly state: "I don't have enough information in your documents to answer this question accurately."
8. NEVER make up information that contradicts or isn't supported by the Reference Data
9. When providing additional context, clearly indicate it's supplementary: "Based on your documents... Additionally, it's worth noting that..."

Your goal is to provide valuable, detailed, and accurate responses grounded in the user's uploaded documents.""")
        ]

        for h in history:
            messages.append(HumanMessage(content=h["human"]))
            messages.append(AIMessage(content=h["assistant"]))

        messages.append(HumanMessage(content=f"User Question: {query}\n\nReference Data:\n{reference_text}"))

        logger.info("Calling Gemini LLM...")
        response = self.llm.invoke(messages).content

        save_message(user_id=user_id, human=query, assistant=response)
        return {"answer": response, "source_documents": retrieved}