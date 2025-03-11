# helper_bot.py

import streamlit as st
from backend.core import retrieve_answer


def handle_chat(prompt: str, selected_workspace: str) -> str:
    """Handles the chat logic, processes user prompt and retrieves the answer."""
    # Make sure workspace is selected
    if not selected_workspace:
        return "Please select a workspace first."

    # Call retrieve_answer function to get the bot's response
    response = retrieve_answer(
        query=prompt,
        workspace_name=selected_workspace,
        chat_history=st.session_state["chat_answer_history"],
    )

    # Format the response with source links
    sources = {doc.metadata["source"] for doc in response["context"]}
    formatted_response = f"{response['answer']} \n\n 📌 **Sources:**\n" + "\n".join(
        f"{i+1}. {src}" for i, src in enumerate(sorted(list(sources)))
    )

    # Update session state with the new conversation
    st.session_state["user_prompt_history"].append(prompt)
    st.session_state["chat_answer_history"].append(formatted_response)

    return formatted_response
