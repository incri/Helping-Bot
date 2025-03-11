import streamlit as st
import os
from ingestion import (
    create_workspace,
    list_workspaces,
    ingest_pdfs,
)

st.title("PDF Vector Store Manager")

# Sidebar for workspace management
st.sidebar.header("Workspace Management")
workspace_name = st.sidebar.text_input("Enter workspace name:")
if st.sidebar.button("Create Workspace"):
    if workspace_name:
        create_workspace(workspace_name)
        st.sidebar.success(f"Workspace '{workspace_name}' created successfully.")
    else:
        st.sidebar.error("Please enter a workspace name.")

st.sidebar.subheader("Existing Workspaces")
workspaces = list_workspaces()
selected_workspace = st.sidebar.selectbox(
    "Select a workspace:", ["-- Select --"] + workspaces
)

# PDF Upload Section
if selected_workspace and selected_workspace != "-- Select --":
    st.subheader(f"Upload PDFs to Workspace: {selected_workspace}")
    uploaded_files = st.file_uploader(
        "Upload PDFs", type=["pdf"], accept_multiple_files=True
    )

    if st.button("Process PDFs"):
        if uploaded_files:
            save_paths = []
            os.makedirs("./uploads", exist_ok=True)
            for uploaded_file in uploaded_files:
                file_path = os.path.join("./uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                save_paths.append(file_path)

            ingest_pdfs(selected_workspace, save_paths)
            st.success("PDFs processed and stored in vector database.")
        else:
            st.error("Please upload at least one PDF.")
