
import streamlit as st
import hmac
from tempfile import NamedTemporaryFile
from utils import paper_to_markdown_noms, model_res_generator, SYSTEM_REVIEWER_PROMPT

st.set_page_config(
    page_title="Paper Review Assistant",
    page_icon="📝",
    # layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Paper review assistant using OLLAMA model",
    }
)

# def check_password():
#     """Returns `True` if the user had the correct password."""

#     def password_entered():
#         """Checks whether a password entered by the user is correct."""
#         if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
#             st.session_state["password_correct"] = True
#             del st.session_state["password"]  # Don't store the password.
#         else:
#             st.session_state["password_correct"] = False

#     # Return True if the password is validated.
#     if st.session_state.get("password_correct", False):
#         return True

#     # Show input for password.
#     st.text_input(
#         "Password", type="password", on_change=password_entered, key="password"
#     )
#     if "password_correct" in st.session_state:
#         st.error("Password incorrect")
#     return False

# if not check_password():
#     st.stop()  # Do not continue if check_password is not True.


# initialize history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

def reset_if_new_file_uploaded():
    st.session_state["messages"] = []

# init variables
md_text = None
init_review_messages = None

st.title("Paper review assistant")


uploaded_file = st.file_uploader("Upload a pdf file",
                                 type=["pdf"],
                                 on_change=reset_if_new_file_uploaded)

if uploaded_file is not None:
    with NamedTemporaryFile(dir='.', suffix='.pdf') as paper:
        paper.write(uploaded_file.getbuffer())
        md_text = paper_to_markdown_noms(paper.name)

        with st.expander("Show paper"):
            st.markdown(md_text)

        if st.session_state["messages"] == []:
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
    # do not display first two messages which is for initial review
    if idx in [0, 1, 3]:
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
# add initial review message after display chat messages from history, otherwise it will be displayed twice
if init_review_messages:
    st.session_state["messages"].extend(init_review_messages)

# continue chat
if prompt := st.chat_input("Enter prompt here.."):
    # add latest message to history in format {role, content}
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message = st.write_stream(model_res_generator(st.session_state["messages"]))
        st.session_state["messages"].append({"role": "assistant", "content": message})
