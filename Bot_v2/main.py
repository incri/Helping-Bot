import os
from dotenv import load_dotenv

import google.generativeai as genai

from langchain_text_splitters import CharacterTextSplitter

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain.chains import create_retrieval_chain

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "❌ Missing API keys! Set GOOGLE_API_KEY and PINECONE_API_KEY in .env."
    )


if __name__ == "__main__":
    pdf_path = "D:/projects/Helping-Bot/Bot_v2/2310.02759v1.pdf"
    pdf_loader = PyPDFLoader(pdf_path)
    documents = pdf_loader.load()
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1500,
        chunk_overlap=200,
    )

    docs = text_splitter.split_documents(documents=documents)
    genai.configure(api_key=GOOGLE_API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = FAISS.from_documents(docs, embeddings)
    vector_store.save_local("faiss_index_react")

    new_vector_store = FAISS.load_local(
        "faiss_index_react", embeddings, allow_dangerous_deserialization=True
    )

    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    retriever = new_vector_store.as_retriever()
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

    query = "tell me about llm algorithm in 5 points"
    print("🔹 Response:", retrieve_answer(query))
