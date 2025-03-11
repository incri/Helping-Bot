import os
import time
import json
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is missing. Check your .env file and ensure dotenv is loaded."
    )


# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
genai.configure(api_key=GOOGLE_API_KEY)

# Directory to store workspace metadata
WORKSPACE_DIR = "./workspaces"
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def create_workspace(workspace_name: str):
    """Creates a new workspace with a unique Pinecone index."""
    index_name = f"workspace-{workspace_name.lower().replace(' ', '-')}-index"

    existing_indexes = pc.list_indexes().names()
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

    # Save workspace metadata
    workspace_metadata = {"name": workspace_name, "index_name": index_name, "files": []}
    with open(os.path.join(WORKSPACE_DIR, f"{workspace_name}.json"), "w") as f:
        json.dump(workspace_metadata, f, indent=4)
    return index_name


def list_workspaces() -> List[str]:
    """Lists all available workspaces."""
    return [
        f.split(".json")[0] for f in os.listdir(WORKSPACE_DIR) if f.endswith(".json")
    ]


def ingest_pdfs(workspace_name: str, pdf_paths: List[str]):
    """Processes and embeds PDFs into the specified workspace."""
    workspace_file = os.path.join(WORKSPACE_DIR, f"{workspace_name}.json")
    if not os.path.exists(workspace_file):
        raise ValueError("Workspace does not exist. Create it first.")

    with open(workspace_file, "r") as f:
        workspace_data = json.load(f)

    index_name = workspace_data["index_name"]
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=50, separators=["\n\n", "\n", " ", ""]
    )
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    all_documents = []
    for pdf_path in pdf_paths:
        pdf_loader = PyPDFLoader(pdf_path)
        raw_documents = pdf_loader.load()
        documents = text_splitter.split_documents(documents=raw_documents)
        all_documents.extend(documents)

        # Save file metadata to workspace
        if pdf_path not in workspace_data["files"]:
            workspace_data["files"].append(pdf_path)

    with open(workspace_file, "w") as f:
        json.dump(workspace_data, f, indent=4)

    print(f"Total documents processed: {len(all_documents)}")
    PineconeVectorStore.from_documents(all_documents, embeddings, index_name=index_name)
