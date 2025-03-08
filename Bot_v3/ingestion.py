import os
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec


def ingest_docs() -> None:

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    pdf_path = "D:/projects/Helping-Bot/Bot_v2/2310.02759v1.pdf"
    pdf_loader = PyPDFLoader(pdf_path)
    documents = pdf_loader.load()

    pc = Pinecone(api_key=PINECONE_API_KEY)
    INDEX_NAME = "helping-bot-v3-embedding-index"

    existing_indexes = pc.list_indexes().names()
    if INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)


if __name__ == "__main__":
    ingest_docs()
