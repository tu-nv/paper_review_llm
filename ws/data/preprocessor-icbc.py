import pandas as pd
import json
import re
import math

# Function to extract specific sections from the review comments
def extract_review_sections(review_text):
    if not isinstance(review_text, str):  # Handle non-string cases
        return "", "", ""
    
    # Use regular expressions to find sections for strengths, shortcomings, and comments
    strength_match = re.search(r'Major strengths of this paper:(.*?)(Major shortcomings|Comments)', review_text, re.DOTALL)
    shortcoming_match = re.search(r'Major shortcomings of this paper:(.*?)(Comments)', review_text, re.DOTALL)
    comment_match = re.search(r'Comments:(.*)', review_text, re.DOTALL)
    
    strength = strength_match.group(1).strip() if strength_match else ""
    shortcoming = shortcoming_match.group(1).strip() if shortcoming_match else ""
    comment = comment_match.group(1).strip() if comment_match else ""
    
    return strength, shortcoming, comment

# Function to process a single paper row into JSON format
def process_paper_with_correct_scores(row):
    # Skip papers with "DeskReject" status
    if row.get('Status') == 'DeskReject':
        return None
    
    # Extract reviewers' comments dynamically based on available reviewers
    reviewers_comments = []
    for i in range(1, 4):  # Assuming up to 3 reviewers
        review_text = row.get(f'Review {i} comments to author', "")
        if pd.notna(review_text):  # Only process if the review exists
            strength, shortcoming, comment = extract_review_sections(review_text)
            reviewer_comment = {
                "strength": strength,
                "shortcoming": shortcoming,
                "comment": comment
            }
            reviewers_comments.append(reviewer_comment)
    
    # Extract scores from the correct columns (Z, AA, AB, AC, AD)
    scores = {
        "Relevance": row.get("review: Relevance", ""),
        "Content and originality": row.get("review: Technical content and originality", ""),
        "Reference": row.get("review: Reference to Related Work", ""),
        "Overall recommendation": row.get("review: Overall Recommendation about accepting the contribution:", ""),
        "Poster acceptance": row.get("review: Poster acceptance", "")
    }
    
    # Check for NaN in scores
    if any(math.isnan(score) for score in scores.values() if isinstance(score, float)):
        return None  # Skip the paper if any score contains NaN
    
    # Check if there are any valid reviews or scores
    has_reviews = any(review["strength"] or review["shortcoming"] or review["comment"] for review in reviewers_comments)
    has_scores = any(scores.values())
    
    # Only include the paper if it has either reviews or scores
    if has_reviews or has_scores:
        paper_json = {
            "number": row["#"],
            "title": row["Title"],
            "abstract": row["Abstract"],
            "review": {
                "strength": [review["strength"] for review in reviewers_comments],
                "shortcoming": [review["shortcoming"] for review in reviewers_comments],
                "comment": [review["comment"] for review in reviewers_comments],
                "score": scores
            }
        }
        return paper_json
    return None  # Return None if no reviews or scores are present

# Main function to convert the Excel file into a JSON file
def convert_excel_to_json(input_excel_file, output_json_file):
    # Load the Excel file
    df = pd.read_excel(input_excel_file, sheet_name='Papers')
    
    # Process all rows in the dataset to generate the JSON for each paper, ignoring papers without reviews or scores
    all_papers_json = [process_paper_with_correct_scores(row) for _, row in df.iterrows()]
    
    # Filter out None values (papers without reviews, scores, or with DeskReject status or NaN scores)
    all_papers_json = [paper for paper in all_papers_json if paper is not None]

    # Save the result to a JSON file
    with open(output_json_file, 'w') as json_file:
        json.dump(all_papers_json, json_file, indent=4)

    print(f"Conversion complete! JSON file saved to {output_json_file}")

# Example usage:
input_excel_file = 'ieeeicbc23-papers.xlsx'  # Replace with your input Excel file path
output_json_file = 'ieeeicbc23-papers.json'  # Replace with your desired output JSON file path

convert_excel_to_json(input_excel_file, output_json_file)
