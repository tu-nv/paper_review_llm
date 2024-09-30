
import streamlit as st
from database import db
import hmac
import copy
import time
from tempfile import NamedTemporaryFile
from utils import paper_to_markdown_noms, model_res_generator, full_response_generator, SYSTEM_REVIEWER_PROMPT, DISCLAMER

st.set_page_config(
    page_title="Paper Review Assistant NOMS 2025",
    page_icon="📝",
    # menu_items={
    #     'About': "Paper review assistant for NOMS 2025",
    # }
)

# initialize history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

def reset_if_new_file_uploaded():
    st.session_state["messages"] = []

# init variables
md_text = None
init_review_messages = None

st.title("Paper review assistant")
st.warning("**Disclaimer**: This LLM-based system assists in reviewing academic papers but does not replace human judgment. Users should verify all suggestions for accuracy and ethical compliance. Use responsibly and adhere to academic standards.")
uploaded_file = st.file_uploader("Upload a paper to start reviewing",
                                 type=["pdf"],
                                 on_change=reset_if_new_file_uploaded)

if uploaded_file is not None:
    with NamedTemporaryFile(dir='.', suffix='.pdf') as paper:
        paper.write(uploaded_file.getbuffer())
        md_text = paper_to_markdown_noms(paper.name)

        with st.expander("Show paper"):
            st.markdown(md_text)

        if st.session_state["messages"] == []:
            paper_review = db.get_paper_review(md_text)
            if paper_review:
                # if not deepcopy, the original paper_review will be updated, and stored in db (cache, although not db.json yet)
                # which can cause unwanted behavior
                st.session_state["messages"] = copy.deepcopy(paper_review["review"])
                time.sleep(4)
            else:
                init_review_messages = [
                                {'role': 'system', 'content': SYSTEM_REVIEWER_PROMPT},
                                {'role': 'user', 'content': md_text}
                            ]
                with st.chat_message("assistant"):
                    reply = st.write_stream(model_res_generator(init_review_messages))
                    init_review_messages.append({'role': 'assistant', 'content': reply})

                init_review_messages.append(
                            {'role': 'user', 'content': " Give a list errors in english writing of the paper, if any."})
                with st.chat_message("assistant"):
                    reply = st.write_stream(model_res_generator(init_review_messages))
                    init_review_messages.append({'role': 'assistant', 'content': reply})

# Display chat messages from history on app rerun
for idx, message in enumerate(st.session_state["messages"]):
    # do not display first two query messages which is for initial review
    if idx in [0, 1, 3]:
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# add initial review message after display chat messages from history, otherwise it will be displayed twice
if init_review_messages:
    st.session_state["messages"].extend(init_review_messages)

# continue chat
if prompt := st.chat_input("Enter prompt here.."):
    if uploaded_file is None:
        st.warning("Please upload a pdf file first.")
        st.stop()
    # add latest message to history in format {role, content}
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message = st.write_stream(model_res_generator(st.session_state["messages"]))
        st.session_state["messages"].append({"role": "assistant", "content": message})
