import pandas as pd
import numpy as np 
import re
from .database import Base, engine, get_db, create_database_tables
from sqlalchemy.orm import Session
from .models import EmailDB
from .chroma import EmailEmbeddingStore


create_database_tables()

EXCLUSION_PATTERN = re.compile(
    r'^\s*["\']?(X-Origin:|X-Folder:|X-Filename:|"X-Origin|-----)', 
    re.IGNORECASE | re.MULTILINE
)

def get_message(Series: pd.Series) -> pd.Series:
    """
    Extracts the message body from raw email text by removing the first 15 header lines.
    
    Args:
        Series: A pandas Series containing raw email messages
        
    Returns:
        A pandas Series with extracted message bodies, stripped of leading/trailing whitespace
    """
    result = pd.Series(index=Series.index)
    for row, message in enumerate(Series):
        message_words = message.split('\n')
        del message_words[:15]
        result.iloc[row] = ''.join(message_words).strip()
    return result

def get_date(Series: pd.Series) -> pd.Series:
    """
    Extracts and parses the date from raw email messages.
    
    Args:
        Series: A pandas Series containing raw email messages
        
    Returns:
        A pandas Series of datetime objects representing email send dates.
        Invalid dates are coerced to NaT (Not a Time).
    """
    result = pd.Series(index=Series.index)
    for row, message in enumerate(Series):
        if pd.isna(message):
             result.iloc[row] = np.nan
             continue
        message_words = message.split('\n')
        del message_words[0]
        del message_words[1:]
        result.iloc[row] = ''.join(message_words).strip()
        result.iloc[row] = result.iloc[row].replace('Date: ', '')
    print('Done parsing, converting to datetime format..')
    return pd.to_datetime(result, errors='coerce') 

def get_sender_and_receiver(Series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Extracts sender and recipient information from raw email messages.
    
    Args:
        Series: A pandas Series containing raw email messages
        
    Returns:
        A tuple of four pandas Series containing:
        - sender: Primary sender email address
        - recipient1: Primary recipient (To:)
        - recipient2: CC recipients
        - recipient3: BCC recipients
    """
    sender = pd.Series(index=Series.index)
    recipient1 = pd.Series(index=Series.index)
    recipient2 = pd.Series(index=Series.index)
    recipient3 = pd.Series(index=Series.index)
    
    for row, message in enumerate(Series):
        if pd.isna(message):
            sender[row], recipient1[row], recipient2[row], recipient3[row] = np.nan, np.nan, np.nan, np.nan
            continue
            
        message_words = message.split('\n')
        if len(message_words) > 12: 
            sender[row] = message_words[2].replace('From: ', '').strip() 
            recipient1[row] = message_words[3].replace('To: ', '').strip() 
            recipient2[row] = message_words[10].replace('X-cc: ', '').strip() 
            recipient3[row] = message_words[11].replace('X-bcc: ', '').strip() 
        else:
             sender[row], recipient1[row], recipient2[row], recipient3[row] = np.nan, np.nan, np.nan, np.nan
        
    return sender, recipient1, recipient2, recipient3

def get_subject(Series: pd.Series) -> pd.Series:
    """
    Extracts the subject line from raw email messages.
    
    Args:
        Series: A pandas Series containing raw email messages
        
    Returns:
        A pandas Series containing email subject lines
    """
    result = pd.Series(index=Series.index)
    
    for row, message in enumerate(Series):
        if pd.isna(message):
             result[row] = np.nan
             continue
             
        message_words = message.split('\n')
        if len(message_words) > 4:
            message_words = message_words[4]
            result[row] = message_words.replace('Subject: ', '').strip()
        else:
            result[row] = np.nan
    return result

def get_folder(Series: pd.Series) -> pd.Series:
    """
    Extracts the folder/mailbox location from raw email messages.
    
    Args:
        Series: A pandas Series containing raw email messages
        
    Returns:
        A pandas Series containing folder paths where emails were stored
    """
    result = pd.Series(index=Series.index)
    
    for row, message in enumerate(Series):
        if pd.isna(message):
             result[row] = np.nan
             continue
             
        message_words = message.split('\n')
        if len(message_words) > 12:
            message_words = message_words[12]
            result[row] = message_words.replace('X-Folder: ', '').strip()
        else:
            result[row] = np.nan
    return result

def insert_to_db(df: pd.DataFrame) -> None:
    """
    Inserts processed email data into the EmailDB database table and ChromaDB in batches.
    """
    print(f"Starting database insertion for {len(df)} records...")
    
    db_generator = get_db()
    db: Session = next(db_generator) 
    
    try:
        new_records = []
        
        for index, row in df.iterrows():
            email_obj = EmailDB(
                sender=row['sender'],
                receiver=row['recipient1'],
                subject=row['Subject'],
                content=row['text'],
                sent_at=row['date'],
            )
            new_records.append(email_obj)
            
            if index % 100 == 0:
                print(f"Prepared {index} records...")
        
        # Add all to database first
        print("Adding records to SQLite database...")
        db.add_all(new_records)
        db.commit()
        print(f"✓ Successfully inserted {len(new_records)} email records into the database.")
        
        # Then add to ChromaDB in batches
        print("\nAdding embeddings to ChromaDB...")
        email_embedding_store = EmailEmbeddingStore()
        email_embedding_store.add_emails_batch(new_records, batch_size=100)
        
    except Exception as e:
        db.rollback()
        print(f"An error occurred during insertion. Transaction rolled back: {e}")
    finally:
        db_generator.close()
        print("Database session closed.")

df = pd.read_csv('experiments/emails.csv')
original_rows = len(df)

df['text'] = get_message(df.message)

df_filtered = df[df['text'].notna()].copy()

filtered_rows = len(df_filtered)
print(f"Original rows: {original_rows}")
print(f"Filtered rows: {filtered_rows}")
print(f"Rows excluded (Non-standard headers): {original_rows - filtered_rows}")

df_filtered['sender'], df_filtered['recipient1'], df_filtered['recipient2'], df_filtered['recipient3'] = get_sender_and_receiver(df_filtered.message)
df_filtered['Subject'] = get_subject(df_filtered.message)
df_filtered['folder'] = get_folder(df_filtered.message)
df_filtered['date'] = get_date(df_filtered.message)

df_filtered = df_filtered.drop(['message', 'file'], axis=1)

insert_to_db(df_filtered)