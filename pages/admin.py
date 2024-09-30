
import streamlit as st
from database import db
import hmac
import copy
from tempfile import NamedTemporaryFile
from utils import paper_to_markdown_noms, model_res_generator, full_response_generator, SYSTEM_REVIEWER_PROMPT

st.set_page_config(
    page_title="Paper Review Assistant NOMS 2025",
    page_icon="📝"
)

# password
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# page start

md_text = None

st.title("Paper review assistant")
st.write("Batch pre-processing and initial reviewing multiple papers and save them in the database.")


# mass upload for pre-processing multiple papers
uploaded_files = st.file_uploader("Upload pdf file(s)",
                                 type=["pdf"],
                                 accept_multiple_files=True)
if uploaded_files is not None and len(uploaded_files) > 0:
    num_files = len(uploaded_files)
    num_file_processed = 0
    file_processing_bar = st.progress(0, text=f"Processing files... {num_file_processed}/{num_files}")

    for file in uploaded_files:
        with NamedTemporaryFile(dir='.', suffix='.pdf') as paper:
            paper.write(file.getbuffer())
            md_text = paper_to_markdown_noms(paper.name)

            init_review_messages = [
                            {'role': 'system', 'content': SYSTEM_REVIEWER_PROMPT},
                            {'role': 'user', 'content': md_text}
                        ]
            reply = full_response_generator(init_review_messages)
            init_review_messages.append({'role': 'assistant', 'content': reply})
            init_review_messages.append({'role': 'user', 'content': " Give a list errors in english writing of the paper, if any."})
            reply = full_response_generator(init_review_messages)
            init_review_messages.append({'role': 'assistant', 'content': reply})

            paper_review = {
                "content": md_text,
                "review": init_review_messages
            }

            db.upsert_paper_review(paper_review)
            num_file_processed += 1
            file_processing_bar.progress(num_file_processed / num_files, text=f"Processing files... {num_file_processed}/{num_files}")
    st.write("Finished.")
