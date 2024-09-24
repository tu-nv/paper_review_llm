import json
from utils import SYSTEM_REVIEWER_PROMPT
from datasets import Dataset
from sklearn.model_selection import train_test_split
paper_review_ds = []
with open('./noms_2024_dataset/noms_2024_all_submissions.json', 'r') as file:
    data = json.load(file)
    for paper in data:
        for review in paper['reviews']:
            paper_review = {
                "instruction": f"{SYSTEM_REVIEWER_PROMPT}\n\n{paper['body']}",
                "output": f"**Strengths**:\n\n{review['strengths']}\n\n**Weaknesses**:\n\n{review['weaknesses']}"
            }
            paper_review_ds.append(paper_review)

paper_review_ds = Dataset.from_list(paper_review_ds).train_test_split(test_size=0.2, seed=42)
trainset = paper_review_ds['train']
testset = paper_review_ds['test']
# trainset, testset = train_test_split(paper_review_ds, test_size=0.2, random_state=42)
