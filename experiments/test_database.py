from sqlalchemy import func
from sqlalchemy.sql.expression import func as sql_func
from .models import EmailDB
from .database import get_db


def get_top_10_senders(db):
    return (
        db.query(EmailDB.sender, func.count(EmailDB.id))
        .group_by(EmailDB.sender)
        .order_by(func.count(EmailDB.id).desc())
        .limit(10)
        .all()
    )


def get_top_10_receivers(db):
    return (
        db.query(EmailDB.receiver, func.count(EmailDB.id))
        .group_by(EmailDB.receiver)
        .order_by(func.count(EmailDB.id).desc())
        .limit(10)
        .all()
    )


def get_highest_receiver_for_sender(db, sender_email: str):
    """
    Finds which receiver the specified sender interacts with most.
    """
    return (
        db.query(EmailDB.receiver, func.count(EmailDB.id).label('email_count'))
        .filter(EmailDB.sender == sender_email)
        .group_by(EmailDB.receiver)
        .order_by(func.count(EmailDB.id).desc())
        .first()
    )


def get_null_sent_at_count(db):
    """
    Returns the count of emails with NULL sent_at values.
    """
    return (
        db.query(func.count(EmailDB.id))
        .filter(EmailDB.sent_at.is_(None))
        .scalar()
    )


def get_random_email_samples(db, n: int = 10):
    """
    Returns n random email samples with their content.
    """
    return (
        db.query(EmailDB.id, EmailDB.sender, EmailDB.receiver, EmailDB.subject, EmailDB.content, EmailDB.sent_at)
        .order_by(sql_func.random())
        .limit(n)
        .all()
    )


if __name__ == "__main__":
    db = next(get_db())

    print("=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    print("\nTop 10 Senders:")
    for sender, count in get_top_10_senders(db):
        print(f"  {sender}: {count}")

    print("\nTop 10 Receivers:")
    for receiver, count in get_top_10_receivers(db):
        print(f"  {receiver}: {count}")

    # Null sent_at count
    null_count = get_null_sent_at_count(db)
    print(f"\nEmails with NULL sent_at: {null_count}")

    # Targeted analysis for top sender
    top_senders = get_top_10_senders(db)
    if top_senders:
        most_active_sender = top_senders[0][0]
        result = get_highest_receiver_for_sender(db, most_active_sender)
        
        if result:
            receiver, count = result
            print(f"\nTargeted Analysis for: {most_active_sender}")
            print(f"  Most frequent recipient: {receiver}")
            print(f"  Total emails sent to them: {count}")

    # Random email samples
    print("\n" + "=" * 60)
    print("10 RANDOM EMAIL SAMPLES")
    print("=" * 60)
    
    samples = get_random_email_samples(db, 10)
    for i, (id, sender, receiver, subject, content, sent_at) in enumerate(samples, 1):
        print(f"\n--- Sample {i} (ID: {id}) ---")
        print(f"From: {sender}")
        print(f"To: {receiver}")
        print(f"Subject: {subject}")
        print(f"Date: {sent_at}")
        print(f"Content preview: {content[:200]}..." if len(content) > 200 else f"Content: {content}")