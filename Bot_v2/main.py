import os
from dotenv import load_dotenv
import google.generativeai as genai

from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub
from langchain.chains import create_retrieval_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS


def load_environment_variables():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ Missing API key! Set GOOGLE_API_KEY in .env.")
    return api_key


def load_pdf(pdf_path: str):
    loader = PyPDFLoader(pdf_path)
    return loader.load()


def split_documents(documents):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1500,
        chunk_overlap=200,
    )
    return text_splitter.split_documents(documents=documents)


def create_vector_store(docs, embeddings, index_name="faiss_index_react"):
    vector_store = FAISS.from_documents(docs, embeddings)
    vector_store.save_local(index_name)
    return vector_store


def load_vector_store(embeddings, index_name="faiss_index_react"):
    return FAISS.load_local(
        index_name, embeddings, allow_dangerous_deserialization=True
    )


def setup_retrieval_chain(vector_store, llm_model="gemini-1.5-pro"):
    retriever = vector_store.as_retriever()
    retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    llm = ChatGoogleGenerativeAI(model=llm_model)
    combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
    return create_retrieval_chain(retriever, combine_docs_chain)


def retrieve_answer(retrieval_chain, query: str):
    response = retrieval_chain.invoke({"input": query})
    print("Raw Response:", response)  # Debugging line
    return response.get("answer", "No valid response received.")


def main():
    GOOGLE_API_KEY = load_environment_variables()
    genai.configure(api_key=GOOGLE_API_KEY)

    pdf_path = "D:/projects/Helping-Bot/Bot_v2/2310.02759v1.pdf"
    documents = load_pdf(pdf_path)
    docs = split_documents(documents)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = create_vector_store(docs, embeddings)

    retrieval_chain = setup_retrieval_chain(vector_store)
    query = "what is full form of AES"
    print("🔹 Response:", retrieve_answer(retrieval_chain, query))


if __name__ == "__main__":
    main()
