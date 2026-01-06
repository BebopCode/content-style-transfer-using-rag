from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from .database import get_db
from .models import EmailDB


def get_highest_receiver():
    """
    Queries the database to find the receiver address that appears most frequently.
    
    Returns: A tuple (receiver_email, count) or None if the table is empty.
    """
    db_generator = get_db()
    db: Session = next(db_generator) 
    
    try:
        highest_receiver_result = db.query(
            EmailDB.receiver,
            func.count(EmailDB.receiver).label('count')
        ).group_by(EmailDB.receiver).order_by(func.count(EmailDB.receiver).desc()).limit(1).first()
        
        if highest_receiver_result:
            receiver_email, count = highest_receiver_result
            print(f" Highest Receiver: **{receiver_email}** (Count: {count})")
            return receiver_email, count
        else:
            print("No records found in the 'email_templates' table.")
            return None
            
    except Exception as e:
        print(f" An error occurred during the query: {e}")
        return None
    finally:
        db_generator.close()


def print_non_empty_references():
    db_generator = get_db()
    db = next(db_generator)

    try:
        emails = db.query(EmailDB).filter(
            and_(
                EmailDB.references.isnot(None),
                EmailDB.references != []
            )
        ).all()

        for email in emails:
            print(email.references)

    finally:
        db_generator.close()


def export_contents_to_file(sender: str, output_file: str = "email_contents.txt"):
    """
    Exports all email contents for a specific sender to a text file.
    
    Args:
        sender: The sender email address to filter by.
        output_file: The output filename (default: email_contents.txt)
    
    Returns:
        The number of emails exported.
    """
    db_generator = get_db()
    db: Session = next(db_generator)
    
    try:
        # Query all emails from the specified sender
        emails = db.query(EmailDB).filter(EmailDB.sender == sender).order_by(EmailDB.sent_at).all()
        
        if not emails:
            print(f"No emails found for sender: {sender}")
            return 0
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Email Contents Export for Sender: {sender}\n")
            f.write(f"Total Emails: {len(emails)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, email in enumerate(emails, 1):
                f.write(f"{'=' * 80}\n")
                f.write(f"EMAIL #{i}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"ID:         {email.id}\n")
                f.write(f"Message ID: {email.message_id}\n")
                f.write(f"Parent ID:  {email.parent_message_id}\n")
                f.write(f"References: {email.references}\n")
                f.write(f"From:       {email.sender}\n")
                f.write(f"To:         {email.receiver}\n")
                f.write(f"Subject:    {email.subject}\n")
                f.write(f"Date:       {email.sent_at}\n")
                f.write(f"{'-' * 80}\n")
                f.write("CONTENT:\n")
                f.write(f"{'-' * 80}\n")
                f.write(f"{email.content}\n")
                f.write("\n\n")
        
        print(f"Exported {len(emails)} emails to '{output_file}'")
        return len(emails)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0
    finally:
        db_generator.close()


def export_all_contents_to_file(output_file: str = "all_email_contents.txt"):
    """
    Exports ALL email contents to a text file (no sender filter).
    
    Args:
        output_file: The output filename (default: all_email_contents.txt)
    
    Returns:
        The number of emails exported.
    """
    db_generator = get_db()
    db: Session = next(db_generator)
    
    try:
        emails = db.query(EmailDB).order_by(EmailDB.sent_at).all()
        
        if not emails:
            print("No emails found in database.")
            return 0
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"All Email Contents Export\n")
            f.write(f"Total Emails: {len(emails)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, email in enumerate(emails, 1):
                f.write(f"{'=' * 80}\n")
                f.write(f"EMAIL #{i}\n")
                f.write(f"{'=' * 80}\n")
                f.write(f"ID:         {email.id}\n")
                f.write(f"Message ID: {email.message_id}\n")
                f.write(f"Parent ID:  {email.parent_message_id}\n")
                f.write(f"References: {email.references}\n")
                f.write(f"From:       {email.sender}\n")
                f.write(f"To:         {email.receiver}\n")
                f.write(f"Subject:    {email.subject}\n")
                f.write(f"Date:       {email.sent_at}\n")
                f.write(f"{'-' * 80}\n")
                f.write("CONTENT:\n")
                f.write(f"{'-' * 80}\n")
                f.write(f"{email.content}\n")
                f.write("\n\n")
        
        print(f"Exported {len(emails)} emails to '{output_file}'")
        return len(emails)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0
    finally:
        db_generator.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # If sender is provided as argument
        sender_email = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "email_contents.txt"
        export_contents_to_file(sender_email, output)
    else:
        # Export all if no sender specified
        export_all_contents_to_file()