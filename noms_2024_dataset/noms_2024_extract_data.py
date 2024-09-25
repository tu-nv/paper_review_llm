from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from utils import paper_to_markdown_noms

PAPER_DIR="noms_2024_all_submissions"

def clean_text(text):
    return text.replace("(\s)+", " ").strip()

# title = "#number: Paper title"
def find_title_number(title):
    pattern = r"^#(\d+)"
    match = re.match(pattern, title)
    if match:
        return match.group(1)  # Extract the number (without the #)
    return None

def find_paper_start_with_number(paper_number, all_paper_files):
    for paper_file in all_paper_files:
        if paper_file.startswith(paper_number):
            return paper_file
    return None

def list_files_in_directory(directory):
    return [f.name for f in Path(directory).iterdir() if f.is_file()]


if __name__ == "__main__":
    all_paper_files = list_files_in_directory(PAPER_DIR)

    with open("noms_2024_all_submissions.html") as file:
        soup = BeautifulSoup(file, 'html.parser')

    paper_reviews = []
    all_submissions = soup.find_all('app-paper-info')
    for submission_html in all_submissions:
        title = submission_html.find('div', class_='main-title').text.strip()
        abstract = submission_html.find('div', class_='section-content abstract').text.strip()

        title_number = find_title_number(title)
        if (title_number is None):
            print(f"Could not find title number for {title}")
            exit(1)

        paper_file = find_paper_start_with_number(title_number, all_paper_files)
        if paper_file is None:
            print(f"Could not find paper for {title}")
            continue

        paper_body = paper_to_markdown_noms(f"{PAPER_DIR}/{paper_file}")

        reviews = []
        review_list_html = submission_html.find('div', class_='paper-review-list')
        for review_html in review_list_html.find_all('div', recursive=False):
            review = {}
            review_parts = review_html.find_all('div', class_="descriptiveField ng-star-inserted")
            for review_part in review_parts:
                aspect = review_part.find(string=True).strip()
                answer = review_part.find_next('div').text.strip()
                answer = clean_text(answer)
                if aspect == '− What are the major strengths of this paper?:':
                    review['strengths'] = answer
                elif aspect == '− What are the major shortcomings of this paper?:':
                    review['weaknesses'] = answer
                elif aspect == '− Detailed comments for the authors:':
                    review['comments'] = answer

            if len(review) != 3:
                print(f'problem for review paper {title}: {review}\n\n')

            reviews.append(review)

        paper_review = {
            'title': title,
            'abstract': abstract,
            'body': paper_body,
            'reviews': reviews
        }
        paper_reviews.append(paper_review)

    with open('noms_2024_all_submissions.json', 'w') as f:
        json.dump(paper_reviews, f, ensure_ascii=False)
        print(f"number of papers: {len(paper_reviews)}")


