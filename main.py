from ollama import Client
import streamlit as st
import torch
import argparse
import pymupdf, pymupdf4llm
import pathlib
from pdf2docx import Converter
from tempfile import NamedTemporaryFile

def parse_args():
    parser = argparse.ArgumentParser(description="Process a boolean flag.")
    parser.add_argument('-o', '--ollama-server-url', type=str, default="http://141.223.124.22:11440", help='ollama server url')
    return parser.parse_args()

args = parse_args()
print(f"Run with args: {args}")

ollama_client = Client(host=args.ollama_server_url , timeout=60)

st.title("Paper review assistant")

# initialize history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# init models
if "model" not in st.session_state:
    st.session_state["model"] = ""

models = [model["name"] for model in ollama_client.list()["models"]]
st.session_state["model"] = st.selectbox("Choose your model", models)

def model_res_generator():
    stream = ollama_client.chat(
        model=st.session_state["model"],
        messages=st.session_state["messages"],
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]


uploaded_file = st.file_uploader("Upload a pdf file", type=["pdf"])
if uploaded_file is not None:
    with NamedTemporaryFile(dir='.', suffix='.pdf') as paper:
        paper.write(uploaded_file.getbuffer())
        md_text = pymupdf4llm.to_markdown(paper.name, margins=(30, 40, 30, 40), dpi=300)

        with st.popover("Show paper", use_container_width=False, disabled=False):
            with st.container(height=600):
                st.write(md_text)

# Display chat messages from history on app rerun
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter prompt here.."):
    # add latest message to history in format {role, content}
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message = st.write_stream(model_res_generator())
        st.session_state["messages"].append({"role": "assistant", "content": message})
