import pandas as pd
import numpy as np 
import re
from datetime import datetime
from typing import List, Optional
from email.utils import parsedate_to_datetime
from .database import Base, engine, get_db, create_database_tables
from sqlalchemy.orm import Session
from .models import EmailDB
from .chroma import EmailEmbeddingStore 


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse email date string to datetime object.
    Uses email.utils.parsedate_to_datetime which handles RFC 2822 format.
    Format example: "Wed, 18 Apr 2001 11:22:00 -0700 (PDT)"
    """
    if pd.isna(date_str) or date_str == '':
        return None
    
    try:
        dt = parsedate_to_datetime(str(date_str))
        # Convert to timezone-naive datetime for SQLite compatibility
        return dt.replace(tzinfo=None)
    except Exception:
        # Fallback to dateutil parser
        try:
            from dateutil import parser
            dt = parser.parse(str(date_str))
            if dt.tzinfo:
                return dt.replace(tzinfo=None)
            return dt
        except Exception:
            return None


def clean_message_id(message_id_str: str) -> str:
    """
    Clean and extract message ID from angle brackets if present.
    Format example: "<ABCD1234@example.com>" -> "ABCD1234@example.com"
    """
    if pd.isna(message_id_str) or message_id_str == '':
        return ''
    
    match = re.search(r'<([^>]+)>', str(message_id_str))
    if match:
        return match.group(1).strip()
    return str(message_id_str).strip()


def extract_references(message: str) -> Optional[List[str]]:
    """
    Extract message IDs from References header in the raw message.
    Returns a list of referenced message IDs.
    """
    if pd.isna(message):
        return None
    
    try:
        # Look for References: header
        ref_match = re.search(r'References:\s*(.+?)(?:\n\S|\Z)', message, re.IGNORECASE | re.DOTALL)
        if ref_match:
            ref_line = ref_match.group(1)
            # Extract all message IDs (format: <...>)
            message_ids = re.findall(r'<([^>]+)>', ref_line)
            return message_ids if message_ids else None
    except Exception as e:
        print(f"Warning: Could not extract references: {e}")
    
    return None


def extract_parent_message_id(message: str, subject: str) -> Optional[str]:
    """
    Extract parent message ID from In-Reply-To header or References.
    """
    if pd.isna(message):
        return None
    
    try:
        # Look for In-Reply-To: header (most direct parent)
        reply_match = re.search(r'In-Reply-To:\s*<([^>]+)>', message, re.IGNORECASE)
        if reply_match:
            return reply_match.group(1)
        
        # Fallback: get last reference (immediate parent)
        references = extract_references(message)
        if references and len(references) > 0:
            return references[-1]  # Last reference is usually the immediate parent
    except Exception as e:
        print(f"Warning: Could not extract parent message ID: {e}")
    
    return None


def clean_email_address(email_str: str) -> str:
    """
    Clean and normalize email addresses.
    Extracts email from formats like 'Name <email@example.com>'
    """
    if pd.isna(email_str):
        return ""
    
    # Extract email from angle brackets if present
    match = re.search(r'<([^>]+)>', str(email_str))
    if match:
        return match.group(1).strip().lower()
    
    return str(email_str).strip().lower()


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the Enron dataset to match the EmailDB schema.
    """
    print("Starting dataframe preprocessing...")
    
    # Create a copy to avoid modifying original
    processed_df = df.copy()
    
    # 1. Handle Message-ID - clean and extract from angle brackets
    processed_df['message_id'] = processed_df['Message-ID'].fillna('').apply(clean_message_id)
    
    # 2. Extract parent_message_id and references from raw message
    print("Extracting parent message IDs and references...")
    processed_df['parent_message_id'] = processed_df.apply(
        lambda row: extract_parent_message_id(row['message'], row['Subject']), 
        axis=1
    )
    processed_df['references'] = processed_df['message'].apply(extract_references)
    
    # 3. Clean sender and receiver
    print("Cleaning email addresses...")
    processed_df['sender'] = processed_df['From'].apply(clean_email_address)
    
    # For receiver, use 'To' field (primary recipients)
    processed_df['receiver'] = processed_df['To'].apply(clean_email_address)
    
    # 4. Use 'content' column for email body (already extracted from the dataset)
    processed_df['email_content'] = processed_df['content'].fillna('')
    
    # 5. Handle subject
    processed_df['subject'] = processed_df['Subject'].fillna('(No Subject)')
    
    # 6. Parse dates
    print("Parsing dates...")
    processed_df['sent_at'] = processed_df['Date'].apply(parse_date)
    
    # 7. Remove rows with invalid critical data
    print("Filtering invalid records...")
    initial_count = len(processed_df)
    
    # Only remove records without content
    processed_df = processed_df[processed_df['email_content'] != '']
    
    removed_count = initial_count - len(processed_df)
    print(f"Removed {removed_count} invalid records (missing content). Remaining: {len(processed_df)}")
    
    # Log how many records have None dates or missing senders
    none_dates = processed_df['sent_at'].isna().sum()
    if none_dates > 0:
        print(f"Warning: {none_dates} records have unparseable dates (will be stored as NULL)")
    
    missing_senders = (processed_df['sender'] == '').sum()
    if missing_senders > 0:
        print(f"Warning: {missing_senders} records have missing senders (will be stored as empty string)")

    # 8. Remove exact duplicates based on Message-ID (only for non-empty message_ids)
    print("Removing duplicates...")
    mask = processed_df['message_id'] != ''
    duplicates_in_valid = processed_df[mask].duplicated(subset=['message_id'], keep='first')
    rows_to_drop = processed_df[mask][duplicates_in_valid].index
    duplicate_count = len(rows_to_drop)
    processed_df = processed_df.drop(rows_to_drop)
    print(f"Removed {duplicate_count} duplicate messages.")
    
    # 9. Select and rename columns for database insertion
    final_df = processed_df[[
        'message_id', 
        'parent_message_id',
        'references',
        'sender', 
        'receiver', 
        'email_content', 
        'subject', 
        'sent_at'
    ]].copy()
    
    # Rename for consistency
    final_df = final_df.rename(columns={'email_content': 'content'})
    
    print(f"Preprocessing complete. Final dataset size: {len(final_df)}")
    return final_df


def insert_to_db(df: pd.DataFrame, batch_size: int = 100) -> None:
    """
    Inserts processed email data into the EmailDB database table and ChromaDB in batches.
    
    Args:
        df: Preprocessed DataFrame with columns matching EmailDB schema
        batch_size: Number of records to process in each batch
    """
    print(f"\nStarting database insertion for {len(df)} records...")
    
    db_generator = get_db()
    db: Session = next(db_generator) 
    
    try:
        records = df.to_dict('records')
        new_records = []
        total_records = len(records)
        
        for i, row in enumerate(records):
            try:
                email_obj = EmailDB(
                    message_id=row['message_id'] if row['message_id'] else None,
                    parent_message_id=row['parent_message_id'],
                    references=row['references'] if row['references'] else None,
                    sender=row['sender'],
                    receiver=row['receiver'],
                    subject=row['subject'],
                    content=row['content'],
                    sent_at=row['sent_at'] if pd.notna(row['sent_at']) else None,
                )
                new_records.append(email_obj)
                
                if (i + 1) % 1000 == 0:
                    print(f"Prepared {i + 1}/{total_records} records ({((i + 1)/total_records)*100:.1f}%)...")
                    
            except Exception as e:
                print(f"Error creating email object at index {i}: {e}")
                continue
        
        # Add all to SQLite database first
        print(f"\nAdding {len(new_records)} records to SQLite database...")
        db.add_all(new_records)
        db.commit()
        print(f"✓ Successfully inserted {len(new_records)} email records into the database.")
        
        # Then add to ChromaDB in batches
        print("\nAdding embeddings to ChromaDB...")
        email_embedding_store = EmailEmbeddingStore()
        email_embedding_store.add_emails_batch(new_records, batch_size=batch_size)
        print("✓ Successfully added embeddings to ChromaDB.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ An error occurred during insertion. Transaction rolled back: {e}")
        raise
    finally:
        db_generator.close()
        print("Database session closed.")


def load_and_process_enron_data(csv_path: str, batch_size: int = 100) -> None:
    """
    Main function to load, preprocess, and insert Enron email data.
    
    Args:
        csv_path: Path to the Enron emails CSV file
        batch_size: Batch size for ChromaDB insertion
    """
    print("="*80)
    print("ENRON EMAIL DATA PROCESSING PIPELINE")
    print("="*80)
    
    # 1. Load the CSV
    print(f"\nLoading CSV from: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} records with {len(df.columns)} columns")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    # 2. Preprocess the data
    try:
        processed_df = preprocess_dataframe(df)
    except Exception as e:
        print(f"❌ Error during preprocessing: {e}")
        return
    
    # 3. Create database tables if they don't exist
    print("\nCreating database tables...")
    create_database_tables()
    
    # 4. Insert into databases
    try:
        insert_to_db(processed_df, batch_size=batch_size)
    except Exception as e:
        print(f"❌ Error during database insertion: {e}")
        return
    
    print("\n" + "="*80)
    print("PROCESSING COMPLETE!")
    print("="*80)


# Example usage
if __name__ == "__main__":
    # Update this path to your actual CSV file location
    CSV_FILE_PATH = "experiments/emails_cleaned.csv"
    
    load_and_process_enron_data(
        csv_path=CSV_FILE_PATH,
        batch_size=100  # Adjust batch size based on your system memory
    )