import pandas as pd
import numpy as np 
from .database import Base, engine, get_db, create_database_tables
from sqlalchemy.orm import Session
from .models import EmailDB
from .utils import embedding_to_blob, emb
import os
import glob
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr
import pprint
# Import your database setup
# Adjust these imports based on your actual folder structure

def parse_eml_file(filepath):
    """
    Reads a .eml file and returns a dictionary ready for the database.
    """
    with open(filepath, 'rb') as f:
        # Use default policy to handle standard email quirks automatically
        msg = BytesParser(policy=policy.default).parse(f)
    def extract_email(header_value):
        """
        Input: 'Aaryan Bhandari <bhandariaaryan16@gmail.com>'
        Output: 'bhandariaaryan16@gmail.com'
        """
        if not header_value:
            return ""
        # parseaddr returns a tuple: ('Real Name', 'email@address.com')
        # We only want the second part [1]
        name, email_address = parseaddr(header_value)
        return email_address
    # 1. Basic Headers
    subject = msg.get('subject', '')
    sender_raw = msg.get('from', '')
    sender = extract_email(sender_raw)
    
    receiver_raw = msg.get('to', '')
    receiver = extract_email(receiver_raw)
    msg_id = msg.get('message-id', '').strip()
    
    # 2. Threading Headers
    in_reply_to = msg.get('in-reply-to', None)
    if in_reply_to:
        in_reply_to = in_reply_to.strip()
        
    # Handle References (Convert string to list for JSON column)
    # Header looks like: "<id1> <id2> <id3>"
    references_raw = msg.get('references', '')
    references_list = references_raw.split() if references_raw else []

    # 3. Date Parsing (Critical for sorting)
    date_str = msg.get('date')
    sent_at = None
    if date_str:
        try:
            sent_at = parsedate_to_datetime(date_str)
        except Exception:
            # Fallback if date is malformed
            sent_at = datetime.now()

    # 4. Body Extraction (Prefer Plain Text, fall back to HTML)
    content = ""
    body = msg.get_body(preferencelist=('plain', 'html'))
    if body:
        try:
            content = body.get_content()
        except Exception:
            content = "[Could not decode content]"

    return {
        "message_id": msg_id,
        "parent_message_id": in_reply_to,
        "references": references_list,
        "sender": sender,
        "receiver": receiver,
        "subject": subject,
        "content": content,
        "sent_at": sent_at,
        "embedding": None # Placeholder
    }

def ingest_folder(folder_path):
    db_generator = get_db()
    db: Session = next(db_generator) 
    # Ensure tables exist
    create_database_tables()
    
    # Get all .eml files
    files = glob.glob(os.path.join(folder_path, "*.eml"))
    print(f"Found {len(files)} .eml files. Parsing...")

    parsed_emails = []

    # 1. Parse all files into memory
    for filepath in files:
        try:
            email_data = parse_eml_file(filepath)
            # specific check: skip if no message_id (garbage file)
            if email_data['message_id']:
                parsed_emails.append(email_data)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")

    # 2. SORT BY DATE
    # Crucial: We must insert parents before children to satisfy ForeignKey constraints
    # We sort by 'sent_at', handling None values just in case
    parsed_emails.sort(key=lambda x: x['sent_at'] or datetime.min)

    print("Inserting into database...")
    
    count = 0
    for data in parsed_emails:
        # Check if exists to avoid duplicates
        exists = db.query(EmailDB).filter_by(message_id=data['message_id']).first()
        if not exists:
            # Note: If 'parent_message_id' points to an email NOT in this batch
            # and NOT in the DB, this might fail if strict FKs are on.
            # In SQLite default, it usually allows it.
            
            email_obj = EmailDB(
                message_id=data['message_id'],
                parent_message_id=data['parent_message_id'],
                references=data['references'],
                sender=data['sender'],
                receiver=data['receiver'],
                subject=data['subject'],
                content=data['content'],
                sent_at=data['sent_at'],
                embedding=data['embedding']
            )
            db.add(email_obj)
            count += 1
    
    try:
        db.commit()
        print(f"Successfully inserted {count} emails.")
    except Exception as e:
        db.rollback()
        print(f"Database Error: {e}")
    finally:
        db.close()

def view_first_10_emails():
    """
    Fetches the first 10 emails and prints all their columns nicely.
    """
    db_generator = get_db()
    db = next(db_generator)

    try:
        # 1. Fetch the data
        emails = db.query(EmailDB).limit(10).all()

        if not emails:
            print(" The database is empty!")
            return

        print(f"Found {len(emails)} emails. Showing the first 10:\n")

        # 2. Loop and Print
        for i, email in enumerate(emails, 1):
            print(f"================ EMAIL #{i} ================")
            
            # We convert the SQLAlchemy object to a clean dictionary for printing
            email_data = {
                "ID (Internal)": email.id,
                "Message-ID": email.message_id,
                "Parent-ID": email.parent_message_id,
                "References": email.references, # This will print as a list
                "Sender": email.sender,
                "Receiver": email.receiver,
                "Subject": email.subject,
                "Sent At": email.sent_at,
                "Has Embedding?": "Yes" if email.embedding else "No",
                
                # Truncate content to 200 chars so your terminal stays readable.
                # Remove the [:200] if you really want to see the whole body.
                "Content Preview": (email.content[:200] + "...") if email.content else "[Empty Body]"
            }
            
            # pprint prints dictionaries in a readable, indented format
            pprint.pprint(email_data, indent=4, sort_dicts=False)
            print("\n")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # REPLACE THIS WITH YOUR FOLDER PATH
    MY_EML_FOLDER = "./backend/data_emails" 
    ingest_folder(MY_EML_FOLDER)
    view_first_10_emails()