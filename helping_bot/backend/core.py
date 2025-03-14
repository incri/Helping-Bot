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
import json
from helper.db import chat_histories

# Load environment variables
load_dotenv()

# Retrieve API keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR")

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


def save_chat_to_mongo(workspace_name: str, user_prompt: str, bot_response: str):
    """Saves chat history in MongoDB for the specific workspace."""

    # Format messages to align with LangChain's expectations (role and content)
    chat_message_user = {
        "role": "user",  # 'role' is user
        "content": user_prompt,  # 'content' is the user's message
        "timestamp": time.time(),
    }

    chat_message_bot = {
        "role": "assistant",  # 'role' is assistant
        "content": bot_response,  # 'content' is the bot's response
        "timestamp": time.time(),
    }

    # Check if the workspace already has a chat history document
    existing_chat = chat_histories.find_one({"workspace_name": workspace_name})

    if existing_chat:
        # If exists, update the chat history (append new messages)
        chat_histories.update_one(
            {"workspace_name": workspace_name},
            {
                "$push": {
                    "chat_history": chat_message_user,  # Save user message with role and content
                },
                "$set": {"last_updated": time.time()},
            },
        )

        # Also append the assistant's response to the history
        chat_histories.update_one(
            {"workspace_name": workspace_name},
            {
                "$push": {
                    "chat_history": chat_message_bot,  # Save bot message with role and content
                },
            },
        )

    else:
        # If the workspace doesn't exist, create a new document
        chat_histories.insert_one(
            {
                "workspace_name": workspace_name,
                "chat_history": [
                    chat_message_user,
                    chat_message_bot,
                ],  # Store both user and bot messages as an array of objects
                "last_updated": time.time(),
            }
        )


def retrieve_answer(query: str, workspace_name: str, chat_history: list = []) -> dict:
    # Retrieve chat history from MongoDB for the given workspace
    workspace_chat = chat_histories.find_one({"workspace_name": workspace_name})

    if workspace_chat:
        chat_history = workspace_chat["chat_history"]

    # Load the workspace metadata
    workspace_file = os.path.join(WORKSPACE_DIR, f"{workspace_name}.json")
    if not os.path.exists(workspace_file):
        return "Workspace does not exist."

    with open(workspace_file, "r") as f:
        workspace_data = json.load(f)

    index_name = workspace_data["index_name"]

    # Set up vector store with the selected workspace's index
    vector_store = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    retriever = vector_store.as_retriever()

    # Load and execute retrieval chain
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    rephrase_prompt = hub.pull("langchain-ai/chat-langchain-rephrase")
    combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
    chat_retriever_chain = create_history_aware_retriever(
        llm, retriever, rephrase_prompt
    )

    retrieval_chain = create_retrieval_chain(chat_retriever_chain, combine_docs_chain)

    # Invoke the retrieval chain to get the answer
    response = retrieval_chain.invoke({"input": query, "chat_history": chat_history})

    if "answer" in response:
        # Save the new chat message to MongoDB before returning the response
        save_chat_to_mongo(workspace_name, query, response["answer"])
        return response
    else:
        return {"answer": "No valid response received."}
