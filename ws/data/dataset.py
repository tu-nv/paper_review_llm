import json
from datasets import Dataset

file_paths = ['./data/ieeeicbc24-papers.json', './data/ieeeicbc23-papers.json', './data/ieeecryptoex24-papers.json', './data/ieeecryptoex23-papers.json']

data_set = []

for file_path in file_paths:
    with open(file_path) as f:
        data = json.load(f)
    for paper in data:
        body = paper['body']
        strengths = " ".join(paper['review']['strength'])
        weaknesses = " ".join(paper['review']['shortcoming'])
        comments = " ".join(paper['review']['comment'])
        scores = paper['review']['score']

        paper_review = {
            "instruction": f"""Please provide a review of the following academic paper. Focus on strengths, weaknesses, and additional comments. The paper is formatted as markdown:
            
            '{body}'?
            """,
            "output": f"Strengths:\n\n{strengths}\n\nWeaknesses:\n\n{weaknesses}\n\nComments:\n\n{comments}"
        }
        data_set.append(paper_review)
data_set = Dataset.from_list(data_set)

