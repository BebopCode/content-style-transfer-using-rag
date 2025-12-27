from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from .models import EmailDB
from .database import SessionLocal


def normalize_subject(subject: str) -> str:
    """
    Normalize email subject by removing common prefixes like 'Re:', 'Fw:', 'Fwd:', etc.
    
    Args:
        subject: Original email subject
    
    Returns:
        Normalized subject without prefixes
    """
    if not subject:
        return ""
    
    # Common email subject prefixes to remove
    prefixes = ['re: ', 'RE: ', 'Re: ']
    
    # Convert to lowercase for comparison
    normalized = subject.strip()
    
    # Keep removing prefixes until none are found
    changed = True
    while changed:
        changed = False
        lower_normalized = normalized.lower()
        
        for prefix in prefixes:
            if lower_normalized.startswith(prefix):
                # Remove the prefix
                normalized = normalized[len(prefix):].strip()
                changed = True
                break
    
    return normalized


def get_thread_emails_by_id(db: Session, email_id: int) -> List[EmailDB]:
    """
    Fetch all emails in a thread based on the email ID.
    Finds the email by ID, extracts its subject and sent_at time,
    then retrieves all emails with the same normalized subject that were sent before it.
    
    Args:
        db: SQLAlchemy database session
        email_id: The ID of the reference email
    
    Returns:
        List of EmailDB objects that match the thread, ordered by sent_at ascending
        (does NOT include the reference email itself)
    """
    # First, get the reference email by ID
    reference_email = db.query(EmailDB).filter(EmailDB.id == email_id).first()
    
    if not reference_email:
        print(f"No email found with ID: {email_id}")
        return []
    
    # Normalize the subject
    base_subject = normalize_subject(reference_email.subject)
    
    if not base_subject:
        print(f"Email {email_id} has no valid subject")
        return []
    
    # Get all emails sent before this one
    query = db.query(EmailDB).filter(
        EmailDB.sent_at < reference_email.sent_at
    )
    
    all_emails = query.all()
    
    # Filter by normalized subject
    thread_emails = [
        email for email in all_emails 
        if normalize_subject(email.subject) == base_subject
    ]
    
    # Sort by sent_at ascending (oldest first)
    thread_emails.sort(key=lambda e: e.sent_at)
    
    return thread_emails


def get_thread_context_by_id(db: Session, email_id: int, 
                             separator: str = "\n\n---\n\n") -> str:
    """
    Get concatenated content of all emails in a thread before the specified email.
    
    Args:
        db: SQLAlchemy database session
        email_id: The ID of the reference email
        separator: String to separate emails
    
    Returns:
        Concatenated email content
    """
    thread_emails = get_thread_emails_by_id(db, email_id)
    
    if not thread_emails:
        return ""
    
    return separator.join([email.content for email in thread_emails if email.content])


def get_reference_and_thread(db: Session, email_id: int) -> tuple[Optional[EmailDB], List[EmailDB]]:
    """
    Get both the reference email and its thread emails.
    
    Args:
        db: SQLAlchemy database session
        email_id: The ID of the reference email
    
    Returns:
        Tuple of (reference_email, thread_emails)
    """
    reference_email = db.query(EmailDB).filter(EmailDB.id == email_id).first()
    
    if not reference_email:
        return None, []
    
    thread_emails = get_thread_emails_by_id(db, email_id)
    
    return reference_email, thread_emails


def print_thread_summary(db: Session, email_id: int):
    """
    Print a summary of the email thread for a given email ID.
    
    Args:
        db: SQLAlchemy database session
        email_id: The ID of the reference email
    """
    reference_email, thread_emails = get_reference_and_thread(db, email_id)
    
    if not reference_email:
        print(f"No email found with ID: {email_id}")
        return
    
    print("\n" + "="*60)
    print("EMAIL THREAD SUMMARY")
    print("="*60)
    print(f"Reference Email ID: {email_id}")
    print(f"Subject: {reference_email.subject}")
    print(f"Normalized subject: {normalize_subject(reference_email.subject)}")
    print(f"Reference email sent at: {reference_email.sent_at}")
    print(f"Emails in thread (before this email): {len(thread_emails)}")
    print("="*60)
    
    if not thread_emails:
        print("No previous emails found in this thread.")
        return
    
    print("\nThread emails (chronological order):")
    for i, email in enumerate(thread_emails, 1):
        sent_time = email.sent_at.strftime("%Y-%m-%d %H:%M:%S") if email.sent_at else "Unknown"
        print(f"\n{i}. ID: {email.id}")
        print(f"   Subject: {email.subject}")
        print(f"   From: {email.sender} → To: {email.receiver}")
        print(f"   Sent: {sent_time}")
        content_preview = email.content[:100] + "..." if len(email.content) > 100 else email.content
        print(f"   Preview: {content_preview}")


# Example usage
if __name__ == "__main__":
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Example 1: Get thread emails by ID
        email_id = 410005  # Replace with actual email ID
        
        print(f"Fetching thread for email ID: {email_id}")
        thread_emails = get_thread_emails_by_id(db, email_id)
        
        print(f"\nFound {len(thread_emails)} emails in the thread")
        
        # Print detailed summary
        print_thread_summary(db, email_id)
        
        # Example 2: Get thread context as string
        print("\n" + "="*60)
        print("Thread Context as String")
        print("="*60)
        
        thread_context = get_thread_context_by_id(db, email_id)
        print(f"Thread context length: {len(thread_context)} characters")
        if thread_context:
            print(f"Preview:\n{thread_context[:300]}...")
        
        # Example 3: Get both reference and thread
        print("\n" + "="*60)
        print("Reference Email and Thread")
        print("="*60)
        
        reference, thread = get_reference_and_thread(db, email_id)
        
        if reference:
            print(f"Reference Email:")
            print(f"  ID: {reference.id}")
            print(f"  Subject: {reference.subject}")
            print(f"  Sent at: {reference.sent_at}")
            print(f"\nPrevious emails in thread: {len(thread)}")
        
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("Thread fetcher completed!")
    print("="*60)