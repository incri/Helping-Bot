import streamlit as st
from typing import Set
from backend.core import retrieve_answer

st.title("🤖 The Helping Bot")
st.markdown("**Built using LangChain and powered by Google Gemini AI**")

# Initialize session state for chat history
if "user_prompt_history" not in st.session_state:
    st.session_state["user_prompt_history"] = []
if "chat_answer_history" not in st.session_state:
    st.session_state["chat_answer_history"] = []

# User Input Box
prompt = st.text_input(
    "💬 **Ask me anything:**", placeholder="Type your question here..."
)


# Function to format sources
def create_sources_string(sources_url: Set[str]) -> str:
    if not sources_url:
        return ""
    sources_list = sorted(list(sources_url))
    return "📌 **Sources:**\n" + "\n".join(
        f"{i+1}. {src}" for i, src in enumerate(sources_list)
    )


# Process user input
if prompt:
    with st.spinner("Thinking..."):
        generate_response = retrieve_answer(query=prompt)
        sources = {doc.metadata["source"] for doc in generate_response["context"]}
        formatted_response = (
            f"{generate_response['answer']} \n\n {create_sources_string(sources)}"
        )

        # Store conversation history
        st.session_state["user_prompt_history"].append(prompt)
        st.session_state["chat_answer_history"].append(formatted_response)

# Display chat history with better UI
st.markdown("---")  # Separator for chat messages
if st.session_state["chat_answer_history"]:
    for user_query, response in zip(
        st.session_state["user_prompt_history"], st.session_state["chat_answer_history"]
    ):
        # User Message (Right Aligned)
        with st.container():
            st.markdown(
                f"""
                <div style="background-color:#dcf8c6; padding:10px; border-radius:10px; margin:5px 40px 5px auto; width:fit-content; max-width:70%;">
                    <b>You:</b><br> {user_query}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Bot Response (Left Aligned)
        with st.container():
            st.markdown(
                f"""
                <div style="background-color:#f0f0f0; padding:10px; border-radius:10px; margin:5px auto 5px 40px; width:fit-content; max-width:70%;">
                    <b>Bot:</b><br> {response}
                </div>
                """,
                unsafe_allow_html=True,
            )
