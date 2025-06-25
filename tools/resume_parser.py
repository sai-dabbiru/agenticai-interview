from langchain.document_loaders import PyPDFLoader

def load_resume_text(pdf_path: str) -> str:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    return " ".join([doc.page_content for doc in docs])
