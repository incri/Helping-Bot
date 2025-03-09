import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub

# Load environment variables
load_dotenv()

# Retrieve API keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not GOOGLE_API_KEY or not PINECONE_API_KEY:
    raise ValueError(
        "❌ Missing API keys! Set GOOGLE_API_KEY and PINECONE_API_KEY in .env."
    )

# Configure Gemini AI
genai.configure(api_key=GOOGLE_API_KEY)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX_NAME = "helping-bot-v3-embedding-index"

vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

# Load Retrieval QA Chain
retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
retriever = vector_store.as_retriever()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)


def retrieve_answer(query: str):
    response = retrieval_chain.invoke({"input": query})

    if "answer" in response:
        return response["answer"]
    else:
        print("⚠️ 'answer' key not found in response!")
        return "No valid response received."


if __name__ == "__main__":
    query = "How does Automated Essay Scoring (AES) differ from conventional evaluation methods, and what is the primary goal of the research discussed in the document?"
    print("🔹 Response:", retrieve_answer(query))
