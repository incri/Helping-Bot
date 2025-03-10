import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
import warnings

# Load environment variables
load_dotenv()

# Retrieve API keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not GOOGLE_API_KEY or not PINECONE_API_KEY:
    raise ValueError(
        "❌ Missing API keys! Set GOOGLE_API_KEY and PINECONE_API_KEY in .env."
    )

warnings.filterwarnings(
    "ignore", category=UserWarning, message=".*LangSmithMissingAPIKeyWarning.*"
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
rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
retriever = vector_store.as_retriever()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
chat_retriever_chain = create_history_aware_retriever(llm, retriever, rephrase_prompt)

retrieval_chain = create_retrieval_chain(chat_retriever_chain, combine_docs_chain)


def retrieve_answer(query: str, chat_history: list[dict[str, any]] = []) -> any:
    response = retrieval_chain.invoke({"input": query, "chat_history": chat_history})

    if "answer" in response:
        return response
    else:
        print("⚠️ 'answer' key not found in response!")
        return "No valid response received."
