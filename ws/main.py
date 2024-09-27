
import streamlit as st
from tempfile import NamedTemporaryFile
from utils import paper_to_markdown, model_res_generator, SYSTEM_PROMPT

# initialize history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

def reset_if_new_file_uploaded():
    st.session_state["messages"] = []

# init variables
md_text = None
init_review_message = None

st.title("Paper review assistant")

uploaded_file = st.file_uploader("Upload a pdf file",
                                 type=["pdf"],
                                 on_change=reset_if_new_file_uploaded)

if uploaded_file is not None:
    with NamedTemporaryFile(dir='.', suffix='.pdf') as paper:
        paper.write(uploaded_file.getbuffer())
        md_text = paper_to_markdown(paper.name)

        with st.popover("Show paper", disabled=False):
            with st.container(height=600):
                st.write(md_text)

        if st.session_state["messages"] == []:
            st.session_state["messages"].extend(
                        [{'role': 'system', 'content': SYSTEM_PROMPT},
                        {'role': 'user', 'content': md_text}])
            with st.chat_message("assistant"):
                init_review_message = st.write_stream(model_res_generator(st.session_state["messages"]))


# Display chat messages from history on app rerun
for idx, message in enumerate(st.session_state["messages"]):
    # do not display first two messages which is for initial review
    if idx < 2:
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# add initial review message after display chat messages from history, otherwise it will be displayed twice
if init_review_message:
    st.session_state["messages"].append({"role": "assistant", "content": init_review_message})
# continue chat
if prompt := st.chat_input("Enter prompt here.."):
    # add latest message to history in format {role, content}
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Store previous assistant message count
    prev_assistant_count = len([msg for msg in st.session_state["messages"] if msg["role"] == "assistant"])
    
    with st.chat_message("assistant"):
        message = st.write_stream(model_res_generator(st.session_state["messages"]))
        st.session_state["messages"].append({"role": "assistant", "content": message})
    
    # Avoid reusing assistant response
    new_assistant_count = len([msg for msg in st.session_state["messages"] if msg["role"] == "assistant"])
    if new_assistant_count > prev_assistant_count:
        st.session_state["messages"] = st.session_state["messages"][:-1]  # Remove duplicate assistant message
