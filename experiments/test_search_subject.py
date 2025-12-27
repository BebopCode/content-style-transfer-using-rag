from sqlalchemy.orm import Session
from .models import EmailDB  # Import your EmailDB class

def get_email_ids_by_subject_substring(db: Session, substring: str):
    """
    Searches for emails where the subject contains the substring.
    Returns a list of IDs.
    """
    # Use .ilike() for case-insensitive search (e.g., 'invoice' matches 'Invoice')
    # The '%' symbols are wildcards representing any number of characters
    results = db.query(EmailDB.id).filter(EmailDB.subject.ilike(f"%{substring}%")).all()
    
    # Extract the IDs from the list of tuples returned by SQLAlchemy
    return [r.id for r in results]

# --- Usage Example ---
if __name__ == "__main__":
    from .database import SessionLocal

    db = SessionLocal()
    try:
        search_term = "Re: WT-1 Electric Service Agreement"
        matching_ids = get_email_ids_by_subject_substring(db, search_term)
        
        print(f"IDs of emails containing '{search_term}': {matching_ids}")
    finally:
        db.close()