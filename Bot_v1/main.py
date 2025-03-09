import os
import time
import re
from dotenv import load_dotenv
import google.generativeai as genai
import google.api_core.exceptions
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_google_genai import ChatGoogleGenerativeAI
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
INDEX_NAME = "helping-bot-embedding-index"


# Ensure Pinecone index exists
def ensure_pinecone_index(index_name: str, dimension: int = 768):
    existing_indexes = pc.list_indexes().names()
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)


ensure_pinecone_index(INDEX_NAME)
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)


# Function to split text by punctuation
def split_by_punctuation(text: str):
    return [segment.strip() for segment in re.split(r"[.?!]", text) if segment.strip()]


# Query Gemini with retry logic
def ask_gemini(query: str, max_retries: int = 3, wait_time: int = 10) -> str:
    model = genai.GenerativeModel("gemini-1.5-pro")
    for attempt in range(max_retries):
        try:
            response = model.generate_content(query)
            return response.text if response else ""
        except google.api_core.exceptions.ResourceExhausted:
            print(f"⚠️ API quota exceeded! Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            break
    return "⚠️ Failed to get response due to API limit."


# Process text and store embeddings
def process_and_store_text(file_path: str):
    print("📌 Processing document...")
    loader = TextLoader(file_path)
    document = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(document)
    print(f"📄 Total text chunks: {len(texts)}")

    summarized_chunks = []
    for i, text in enumerate(texts):
        print(f"🔍 Processing chunk {i+1}/{len(texts)}...")
        split_texts = split_by_punctuation(text.page_content[:500])
        summarized_text = " ".join(
            ask_gemini(f"Summarize this: {sentence}") for sentence in split_texts
        )
        summarized_chunks.append(summarized_text)

    print("🛠 Generating embeddings and storing in Pinecone...")
    embeddings_list = embeddings.embed_documents(summarized_chunks)
    ids = [f"chunk-{i}" for i in range(len(summarized_chunks))]
    vector_store.add_texts(summarized_chunks, ids=ids, embeddings=embeddings_list)
    print("✅ Summarized data successfully stored in Pinecone!")


# Add Retrieval Feature
retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
retriever = vector_store.as_retriever()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)


def retrieve_answer(query: str):
    response = retrieval_chain.invoke({"input": query})
    print("Raw Response:", response)  # Debugging line

    if "answer" in response:  # Change "output" to "answer"
        return response["answer"]
    else:
        print("⚠️ 'answer' key not found in response!")
        return "No valid response received."


if __name__ == "__main__":
    print("📌 Gemini + Pinecone Setup Completed!")
    process_and_store_text("D:/langchain.txt")
    query = "Tell me about baibhav paudel and what he is doing and should plan next in short"
    print("🔹 Response:", retrieve_answer(query))
