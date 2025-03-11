import streamlit as st
from frontend.workspace import (
    handle_pdf_upload,
    create_workspace,
    list_workspaces,
)
from frontend.helper_bot import handle_chat


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
    workspaces = list_workspaces()
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

        # User input for chat
        # Create a form for user input

        with st.form(key="chat_form", clear_on_submit=True):
            prompt = st.text_input(
                "💬 **Ask me anything:**", placeholder="Type your question here..."
            )
            # Submit button for sending the query
            submit_button = st.form_submit_button("Submit")

        # Handle submission and call the chat function
        if submit_button and prompt:
            with st.spinner("Thinking..."):
                # Call the helper_bot to handle chat
                response = handle_chat(prompt, selected_workspace)
                # Clear the form by setting the prompt to an empty string
                st.session_state.prompt = ""

        # Display chat history with better UI\
        st.markdown("---")  # Separator for chat messages
        if st.session_state["chat_answer_history"]:
            for user_query, response in zip(
                st.session_state["user_prompt_history"],
                st.session_state["chat_answer_history"],
            ):
                # Display User Message
                with st.container():
                    st.markdown(
                        f"<div style='background-color:#dcf8c6; padding:10px; border-radius:10px; margin:5px 40px 5px auto; width:fit-content; max-width:70%;'><b>You:</b><br>{user_query}</div>",
                        unsafe_allow_html=True,
                    )

                # Display Bot Response
                with st.container():
                    st.markdown(
                        f"<div style='background-color:#f0f0f0; padding:10px; border-radius:10px; margin:5px auto 5px 40px; width:fit-content; max-width:70%;'><b>Bot:</b><br>{response}</div>",
                        unsafe_allow_html=True,
                    )


if __name__ == "__main__":
    main()
