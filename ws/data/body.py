import os
import json
import pymupdf
import re

def clean_text(in_text):
    text = re.sub(r'(-\n){1,}', '', in_text)
    text = re.sub(r'\n{1,}', ' ', text)
    text = re.sub(r'\s{1,}', ' ', text)
    text = re.sub(r'-\xad', '-', text)
    text = re.sub(r'^\s+', '', text)
    text = re.sub(r'\s+$', '', text)
    text = re.sub(r'([A-Z])\s([A-Z]+)', r'\1\2', text)
    return text.strip()

def extract_paper_parts(pdf_path):
    paper_md = []
    start_saving = False  # Flag to track when to start saving content
    with pymupdf.open(pdf_path) as doc:  # open document
        for idx, page in enumerate(doc):
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:
                    continue

                text = ""
                is_bolds = []
                for line in block["lines"]:
                    for span in line["spans"]:
                        text += span["text"] + " "
                        is_bolds.append(span["flags"] & 2**4)
                text = clean_text(text)
                
                if "i." in text.lower():
                    start_saving = True

                if start_saving:
                    paper_md.append(text)
    return "\n\n".join(paper_md)

# Function to update JSON with PDF content based on the paper number
def update_json_with_pdf_content(json_file_path, pdf_folder):
    # Load the existing JSON file
    with open(json_file_path, 'r') as json_file:
        papers = json.load(json_file)
    
    # Iterate through all PDFs in the specified folder
    for pdf_filename in os.listdir(pdf_folder):
        if pdf_filename.endswith(".pdf"):
            # Extract the paper number from the PDF filename (assuming it's the name of the PDF file)
            paper_number = os.path.splitext(pdf_filename)[0]  # Remove ".pdf" to get the number
            
            # Read the content of the PDF (extracting body only)
            pdf_file_path = os.path.join(pdf_folder, pdf_filename)
            pdf_body = extract_paper_parts(pdf_file_path)
            
            # Update the corresponding entry in the JSON file
            for paper in papers:
                if str(paper["number"]) == paper_number:
                    paper["body"] = pdf_body
                    break  # Exit the loop once the matching paper is found
    
    # Save the updated JSON
    with open(json_file_path, 'w') as json_file:
        json.dump(papers, json_file, indent=4)
    
    print(f"Updated JSON saved to {json_file_path}")

# Example usage
json_file_path = 'ieeecryptoex23-papers.json'  # Replace with your actual JSON file path
pdf_folder = 'ieeecryptoex23-papers'  # Replace with the actual folder containing the PDF files
update_json_with_pdf_content(json_file_path, pdf_folder)
