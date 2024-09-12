import re
import pymupdf
from ollama import Client
import difflib


OLLAMA_SERVER_URL="http://141.223.124.22:11440"
OLLAMA_MODEL="llama3.1:70b"
ollama_options= {
                    'temperature': 0.1,
                    'num_ctx': 20000,
                    'top_p': 0.1,
                    'num_predict': 8192,
                    'num_gpu': 99,
                }
# SYSTEM_PROMPT = "Only fix grammar (syntax, punctuation, spelling). Do not change words, and only if it is necessary, use the same writing style. Use American English spelling, and no contractions (e.g., don't, it's) at all. Output only the fixed text, nothing else. Here is the text:\n"

# SYSTEM_PROMPT = "you are an english writing checker. I give you an academic paper in markdown format. You output a list of grammar and syntax errors with fixes, nothing else. Only fix grammar and syntax errors. Bellow is the paper:\n\n\n"

SYSTEM_PROMPT = """You are an journal paper reviewer. I give you an academic paper in markdown format. Note that all figures, equations, and tables are removed from the paper, only text is available. Review the paper by strictly following the template bellows:

**Strengths**: give a list of strengths of the paper.
**Weaknesses**: give a list of weaknesses of the paper.
**Presentation and writing**: evaluate the presentation and english writing quality of the paper (grammar, syntax, punctuation, spelling).

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
        print(chunk, end='', flush=True)
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


def paper_english_check(text):
    diff_text = []
    for line in text.split("\n\n"):
        if line.startswith("#"):
            diff_text.append(line)
        else:
            diff = diff_words(line, initial_review(line))
            diff_text.append(diff)

    return "\n\n".join(diff_text)


if __name__ == "__main__":
    md_text = paper_to_markdown("ibn_llm.pdf")
    md_diff = initial_review(md_text)
    with open("ibn_llm.md", "w") as md_file:
        md_file.write(md_diff)

