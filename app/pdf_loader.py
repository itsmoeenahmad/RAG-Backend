from pypdf import PdfReader
from langchain_core.documents import Document

def pdf_to_documents(file_path: str):
    """Extract text from PDF and return list of LangChain Document objects (single big doc)."""
    text_parts = []
    reader = PdfReader(file_path)
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_parts.append(page_text)
    full_text = "\n".join(text_parts)
    # Return a single document. Splitting into chunks happens later in vectorstore.
    return [Document(page_content=full_text, metadata={"source": file_path})]