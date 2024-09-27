import re
import pymupdf
from ollama import Client
import difflib


OLLAMA_SERVER_URL="http://127.0.0.1:11434"
OLLAMA_MODEL="my-model3:latest"
ollama_options= {
                    'temperature': 0.2,
                    'num_ctx': 20000,
                    'top_p': 0.1,
                    'num_predict': 4096,
                    'num_gpu': 99,
                }

SYSTEM_PROMPT = """You are an journal paper reviewer. I give you an academic paper in markdown format. Do not mention the lack of tables, figures or equations. Provide specific examples from the paper, and give constructive feedback on areas for improvement. Review the paper by strictly following the template bellows:

**Strengths**: give a list of strengths of the paper.
**Weaknesses**: give a list of weaknesses of the paper. Important: Do not list the weaknesses that are already discussed in the paper, unless you have additional comments.
**Comments**: give some additional comments of the paper.
Here is the paper:

"""

ollama_client = Client(host=OLLAMA_SERVER_URL, timeout=600)


def diff_words(original, modified):
    """Create a word-level diff between original and modified."""
    # Get a diff object using difflib
    diff = difflib.ndiff(original.split(), modified.split())
    diffed_text = []
    for token in diff:
        code = token[0]  # '+', '-', or ' ' for insertion, deletion, or unchanged
        word = token[2:] # Actual word content

        if code == '+':  # Word was added
            diffed_text.append(f'**{word}**')
        elif code == '-':  # Word was removed
            diffed_text.append(f'~~{word}~~')
        else:  # Word is unchanged
            diffed_text.append(word)

    return ' '.join(diffed_text)

def clean_text(in_text):
    text = re.sub(r'(-\n){1,}', '', in_text)
    text = re.sub(r'\n{1,}', ' ', text)
    # soft hyphen
    text = re.sub(r'-\xad', '-', text)
    # clean spaces
    text = re.sub(r'\s{1,}', ' ', text)
    # remove spaces at the beginning of the text
    text = re.sub(r'^\s+', '', text)
    # remove spaces at the end of the text
    text = re.sub(r'\s+$', '', text)
    return text

def model_res_generator(messages):
    stream = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        stream=True,
        options=ollama_options,
    )
    for chunk in stream:
        yield chunk["message"]["content"]

def initial_review(input_text):
    full_response = ""
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': input_text}]

    for chunk in model_res_generator(messages):
        full_response += chunk

    return full_response

def paper_to_markdown(pdf_path):
    paper_md = []
    with pymupdf.open(pdf_path) as doc:  # open document
        for idx, page in enumerate(doc):
            # if idx != 0:
            #     continue
            for block in page.get_text("dict")["blocks"]:
                # only care about text block
                if block["type"] != 0:
                    continue

                text = ""
                is_bolds = []
                for line in block["lines"]:
                    for span in line["spans"]:
                            text += span["text"] + " "
                            # print(span["text"])
                            is_bolds.append(span["flags"] & 2**4)
                text = clean_text(text)

                # only care if first text is bold
                if is_bolds[0]:
                    # return if references
                    if text.lower() == "references":
                        return "\n\n".join(paper_md)

                    # return if references
                    if text.lower() == "abstract":
                        paper_md.append(f'# Abstract')
                        continue

                    # detect section
                    section_number = re.match(r'\d(\.\d)*\s', text)
                    if section_number:
                        num_digit = len(re.findall(r'\d', section_number[0]))
                        paper_md.append(f'{"#"*num_digit} {text}')
                        continue

                # only count ascii characters
                if len(text.encode("ascii", "ignore")) < 50:
                    continue

                paper_md.append(text)

    return "\n\n".join(paper_md)

if __name__ == "__main__":
    md_text = paper_to_markdown("icbc.pdf")
    md_diff = initial_review(md_text)
    with open("icbc.md", "w") as md_file:
        md_file.write(md_diff)

