import streamlit as st
from frontend.workspace import handle_pdf_upload, create_workspace, list_workspaces
from frontend.helper_bot import handle_chat, fetch_chat_history_from_mongo


def main():
    st.title("PDF Vector Store and Helping Bot")

    # Sidebar for workspace management
    st.sidebar.header("Workspace Management")
    workspace_name = st.sidebar.text_input("Enter workspace name:")

    # Creating a workspace
    if st.sidebar.button("Create Workspace"):
        if workspace_name:
            create_workspace(workspace_name)
            st.sidebar.success(f"Workspace '{workspace_name}' created successfully.")
        else:
            st.sidebar.error("Please enter a workspace name.")

    # List and select existing workspaces
    st.sidebar.subheader("Existing Workspaces")
    workspaces = list_workspaces()  # Your function to list workspaces
    selected_workspace = st.sidebar.selectbox(
        "Select a workspace:", ["-- Select --"] + workspaces
    )

    # Clear the input box when workspace is switched
    if "last_workspace" not in st.session_state:
        st.session_state["last_workspace"] = None

    if selected_workspace != st.session_state["last_workspace"]:
        st.session_state["user_prompt_history"] = []
        st.session_state["chat_answer_history"] = []
        st.session_state["last_workspace"] = selected_workspace
        st.session_state["chat_fetched_from_mongo"] = False  # Reset flag
        st.rerun()  # Refresh the page on workspace switch

    # Proceed only if a workspace is selected
    if selected_workspace and selected_workspace != "-- Select --":
        # Handle PDF uploads and indexing for the selected workspace
        handle_pdf_upload(selected_workspace)

        # Bot section - display below the workspace management section
        st.subheader(f"Helping Bot for Workspace: {selected_workspace}")
        st.markdown("**Ask questions related to the PDFs in this workspace.**")

        # Initialize session state for chat history if not already initialized
        if "user_prompt_history" not in st.session_state:
            st.session_state["user_prompt_history"] = []
        if "chat_answer_history" not in st.session_state:
            st.session_state["chat_answer_history"] = []

        st.markdown(
            """
        <style>
            /* Fix the form at the bottom of the screen */
            .stForm {
                position: fixed;
                bottom: 20px; /* Slightly raised from the bottom */
                left: 45%;
                transform: translateX(-25%);
                width: 950px;
                padding: 15px;
                background-color: #f7f7f7; /* Light, neutral background */
                border-radius: 12px;
                box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 14px;
                z-index: 10000;
            }

            .stTextInput input {
                padding: 12px;
                border-radius: 8px;
                font-size: 16px;
                transition: all 0.3s ease;
                width: 800px;
            }

            .stTextInput input:focus {
                border-color: #0073e6;
            }

            /* Style for the submit button */
            .stButton button {
                background-color: #0073e6;
                color: white;
                border-radius: 8px;
                border: none;
                padding: 12px 20px;
                font-size: 16px;
                margin-left: 15px;
                cursor: pointer;
                transition: background-color 0.3s ease, transform 0.2s ease;
            }

            .stButton button:hover {
                background-color: #005bb5;
                transform: translateY(-2px);
            }

            .stButton button:active {
                transform: translateY(0);
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        with st.form(key="chat_form", clear_on_submit=True):
            prompt = st.text_input(
                "💬 **Ask me anything:**", placeholder="Type your question here..."
            )
            submit_button = st.form_submit_button("Submit")

        # Handle submission and call the chat function
        if submit_button:
            if prompt.strip() == "":
                st.error("Please enter a valid question!")
            else:
                with st.spinner("Thinking..."):
                    try:
                        # Call the helper_bot to handle chat
                        response = handle_chat(prompt, selected_workspace)

                        # Append the new chat to session_state
                        st.session_state["user_prompt_history"].append(prompt)
                        st.session_state["chat_answer_history"].append(response)
                        st.session_state.prompt = ""  # Clear the form after submission
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

        # If the workspace history is not fetched yet, fetch from MongoDB
        if not st.session_state.get("chat_fetched_from_mongo", False):
            chat_history = fetch_chat_history_from_mongo(selected_workspace)
            if chat_history:
                # Append MongoDB chat history to session state chat history
                for entry in chat_history:
                    if entry["role"] == "user":
                        st.session_state["user_prompt_history"].append(entry["content"])
                    elif entry["role"] == "assistant":
                        st.session_state["chat_answer_history"].append(entry["content"])

            # Set flag that history has been fetched from MongoDB
            st.session_state["chat_fetched_from_mongo"] = True

    # Display current chat history (session_state + MongoDB history combined)
    if st.session_state["chat_answer_history"]:
        for user_query, response in zip(
            st.session_state["user_prompt_history"],
            st.session_state["chat_answer_history"],
        ):
            if user_query:  # Display user messages
                st.markdown(
                    f"<div style='background-color:#dcf8c6; padding:10px; border-radius:10px; margin:5px 40px 5px auto; width:fit-content; max-width:70%;'><b>You:</b><br>{user_query}</div>",
                    unsafe_allow_html=True,
                )
            if response:  # Display bot responses
                st.markdown(
                    f"<div style='background-color:#f0f0f0; padding:10px; border-radius:10px; margin:5px auto 5px 40px; width:fit-content; max-width:70%;'><b>Bot:</b><br>{response}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"<div style=' padding:14px;  margin:10px auto 5px 40px; width:fit-content; max-width:70%;'></div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
