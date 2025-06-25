from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

embedding_model = OpenAIEmbeddings()

def load_interview_vectorstore() -> FAISS:
    # Add metadata to each document
    documents = [
        Document(page_content="Explain CI/CD pipeline and its stages.", metadata={"domain": "devops"}),
        Document(page_content="What is infrastructure as code?", metadata={"domain": "devops"}),
        Document(page_content="What is a Dockerfile and how do you use it?", metadata={"domain": "devops"}),
        Document(page_content="Explain how Kubernetes handles rolling updates.", metadata={"domain": "devops"}),
        Document(page_content="What is the purpose of AWS CloudFormation?", metadata={"domain": "devops"}),

        Document(page_content="Explain virtual DOM in React.", metadata={"domain": "frontend"}),
        Document(page_content="How does useEffect work in React?", metadata={"domain": "frontend"}),
    ]

    return FAISS.from_documents(documents, embedding_model)
