import re
import pymupdf
from ollama import Client
import difflib
from pdf2docx import Converter



OLLAMA_SERVER_URL="http://localhost:11450"
OLLAMA_MODEL="llama3.1:8b"
# OLLAMA_MODEL="mistral-large"
ollama_options= {
                    'temperature': 0.2,
                    'num_ctx': 20000,
                    'top_p': 0.1,
                    'num_predict': 4096,
                    'num_gpu': 99,
                }
# SYSTEM_PROMPT = "Only fix grammar (syntax, punctuation, spelling). Do not change words, and only if it is necessary, use the same writing style. Use American English spelling, and no contractions (e.g., don't, it's) at all. Output only the fixed text, nothing else. Here is the text:\n"

# SYSTEM_PROMPT = "you are an english writing checker. I give you an academic paper in markdown format. You output a list of grammar and syntax errors with fixes, nothing else. Only fix grammar and syntax errors. Bellow is the paper:\n\n\n"

SYSTEM_REVIEWER_PROMPT = """
You are an journal paper reviewer. I give you an academic paper in markdown format. Do not mention the lack of tables, figures or equations. Provide specific examples from the paper, and give constructive feedback on areas for improvement. Review the paper by strictly following the template bellows:

**Strengths**: give a list of strengths of the paper.
**Weaknesses**: give a list of weaknesses of the paper. Important: Do not list the weaknesses that are already discussed in the paper, unless you have additional comments.
**Presentation**: comment on the presentation of the paper.
**Conclusion**: what is the most significant strength and weakness of the paper?

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
    text = re.sub(r'(-\s\n){1,}', '', in_text)
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

def full_response_generator(messages):
    full_response = ""
    for chunk in model_res_generator(messages):
        full_response += chunk

    return full_response

def initial_review(input_text):
    messages = [{'role': 'system', 'content': SYSTEM_REVIEWER_PROMPT},
                {'role': 'user', 'content': input_text}]

    return full_response_generator(messages)

# for noms
def paper_to_markdown_noms(pdf_path):
    paper_md = []
    with pymupdf.open(pdf_path) as doc:  # open document
        start_introduction = False
        for idx, page in enumerate(doc):
            page.set_cropbox(page.cropbox + [40, 40, -40, -40])

            for block in page.get_text("dict")["blocks"]:
                # only care about text block
                if block["type"] != 0:
                    continue

                block_text = ""
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        # print(span)
                        line_text += span["text"]
                    block_text += line_text + "\n"
                text = clean_text(block_text)

                # return if references
                if text.lower() == "references":
                    return "\n\n".join(paper_md)

                # detect section
                section_number = re.match(r'^(I{1,3}|IV|V|VI{1,3}|IX)\.\s[A-Z\s]+', text)
                if section_number:
                    paper_md.append(f'{text}')
                    start_introduction = True
                    continue

                # only count ascii characters
                if len(text.encode("ascii", "ignore")) < 50:
                    continue
                if start_introduction:
                    paper_md.append(text)

    return "\n\n".join(paper_md)

# for ijnm review paper only
def paper_to_markdown_ijnm(pdf_path):
    paper_md = []
    with pymupdf.open(pdf_path) as doc:  # open document
        for idx, page in enumerate(doc):
            # skip the first pages which is not the paper content
            if idx == 0:
                continue
            page.set_cropbox(page.cropbox + [40, 40, -40, -40])

            for block in page.get_text("dict")["blocks"]:
                # only care about text block
                if block["type"] != 0:
                    continue

                block_text = ""
                is_bolds = []
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        # print(span)
                        line_text += span["text"] + " "
                        is_bolds.append(span["flags"] & 2**4)
                    block_text += line_text + "\n"
                text = clean_text(block_text)

                # only care if first text is bold
                if is_bolds[0] and len(text.encode("ascii", "ignore")) < 50:
                    # return if references
                    if text.lower() == "references":
                        return "\n\n".join(paper_md)

                    # return if references
                    if text.lower() in ["abstract", "summary"]:
                        paper_md.append(f'# {text}')
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
    # convert pdf to docx
    # cv = Converter("noms.pdf")
    # cv.convert("noms.docx")      # all pages by default
    # cv.close()
    md_text = paper_to_markdown_noms("noms.pdf")
    # md_text = initial_review(md_text)
    with open("noms.md", "w") as md_file:
        md_file.write(md_text)

