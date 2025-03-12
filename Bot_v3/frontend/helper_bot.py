import streamlit as st
from backend.core import retrieve_answer
from helper.db import chat_histories


def fetch_chat_history_from_mongo(workspace_name: str):
    """Fetches the chat history from MongoDB for the specific workspace."""
    workspace_chat = chat_histories.find_one({"workspace_name": workspace_name})
    if workspace_chat:
        return workspace_chat["chat_history"]
    return []  # Return an empty list if no history exists


def handle_chat(prompt: str, selected_workspace: str) -> str:
    """Handles the chat logic, processes user prompt and retrieves the answer."""
    # Make sure workspace is selected
    if not selected_workspace:
        return "Please select a workspace first."

    # Retrieve previous chat history from MongoDB
    chat_history = fetch_chat_history_from_mongo(selected_workspace)

    # Call retrieve_answer function to get the bot's response
    response = retrieve_answer(
        query=prompt,
        workspace_name=selected_workspace,
        chat_history=chat_history,
    )

    # Format the response with source links
    sources = {doc.metadata["source"] for doc in response["context"]}
    formatted_response = f"{response['answer']} \n\n 📌 **Sources:**\n" + "\n".join(
        f"{i+1}. {src}" for i, src in enumerate(sorted(list(sources)))
    )

    return formatted_response
