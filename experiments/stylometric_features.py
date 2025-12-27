from sqlalchemy.orm import Session
from typing import Tuple
from .models import EmailDB
import spacy
from collections import Counter

def get_historical_context(db: Session, sender: str, receiver: str, number_of_emails: int = 5) -> Tuple[str, str]:
    """
    Retrieve historical email context between a sender and receiver.
    
    This function fetches up to 100 emails from the sender to the receiver,
    concatenates all their content, and separately returns the content of
    the three most recent emails.
    
    Args:
        db: SQLAlchemy database session
        sender: Email address or identifier of the sender
        receiver: Email address or identifier of the receiver
    
    Returns:
        Tuple containing:
        - all_emails_context (str): Concatenated content of up to 100 emails
        - recent_emails_context (str): Concatenated content of 3 most recent emails
    
    Example:
        >>> db = SessionLocal()
        >>> all_context, recent_context = get_historical_context(db, "john@example.com", "sarah@example.com")
        >>> print(f"Total emails context length: {len(all_context)}")
        >>> print(f"Recent emails: {recent_context}")
    """
    
    # Query to get up to 100 emails from sender to receiver, ordered by most recent first
    emails = db.query(EmailDB).filter(
        EmailDB.sender == sender,
        EmailDB.receiver == receiver
    ).order_by(EmailDB.sent_at.desc()).limit(number_of_emails).all()
    
    # If no emails found, return empty strings
    if not emails:
        return "", ""
    
    # Concatenate all email contents (up to 100 emails)
    all_emails_context = "\n\n---\n\n".join([email.content for email in emails if email.content])
    
    # Get the three most recent emails
    recent_emails = emails[:3]  # Already ordered by most recent
    recent_emails_context = "\n\n---\n\n".join([email.content for email in recent_emails if email.content])
    
    return all_emails_context, recent_emails_context


def extract_top_words(text: str, number_of_extractions: int = 5):
    # Load English language model
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    # Initialize counters
    verbs = Counter()
    adverbs = Counter()
    adjectives = Counter()

    # Iterate through tokens
    for token in doc:
        if token.is_alpha:  # ignore punctuation/numbers
            if token.pos_ == "VERB":
                verbs[token.lemma_.lower()] += 1
            elif token.pos_ == "ADV":
                adverbs[token.lemma_.lower()] += 1
            elif token.pos_ == "ADJ":
                adjectives[token.lemma_.lower()] += 1

    # Get top n of each category
    top_verbs = [w for w, _ in verbs.most_common(number_of_extractions)]
    top_adverbs = [w for w, _ in adverbs.most_common(number_of_extractions)]
    top_adjectives = [w for w, _ in adjectives.most_common(number_of_extractions)]

    return {
        "verbs": top_verbs,
        "adverbs": top_adverbs,
        "adjectives": top_adjectives,
    }