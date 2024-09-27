from tinydb import TinyDB, Query

db_path = 'database/db.json'

def upsert_paper_review(paper_review):
    with TinyDB(db_path) as db:
        db.upsert(paper_review, Query().content == paper_review["content"])

def get_paper_review(content):
    with TinyDB(db_path) as db:
        return db.get(Query().content == content)
