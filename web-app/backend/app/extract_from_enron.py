import pandas as pd
import numpy as np 
import re
from .database import Base, engine, get_db, create_database_tables
from sqlalchemy.orm import Session
from .models import EmailDB
# from .utils import embedding_to_blob, emb


create_database_tables()
#  Base.metadata.create_all(bind=engine)

# Define the starting strings to exclude globally so they can be used inside the function
EXCLUSION_PATTERN = re.compile(
    r'^\s*["\']?(X-Origin:|X-Folder:|X-Filename:|"X-Origin|-----)', 
    re.IGNORECASE | re.MULTILINE
)

def get_message(Series: pd.Series):
    result = pd.Series(index=Series.index)
    for row, message in enumerate(Series):
        message_words = message.split('\n')
        del message_words[:15]
        result.iloc[row] = ''.join(message_words).strip()
    return result

# The other functions remain the same, but we will adjust the main script to apply the filter 
# to the whole DataFrame based on the 'text' column after get_message runs.

def get_date(Series: pd.Series):
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

def get_sender_and_receiver(Series: pd.Series):
    sender = pd.Series(index = Series.index)
    recipient1 = pd.Series(index = Series.index)
    recipient2 = pd.Series(index = Series.index)
    recipient3 = pd.Series(index = Series.index)
    
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

def get_subject(Series: pd.Series):
    result = pd.Series(index = Series.index)
    
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

def get_folder(Series: pd.Series):
    result = pd.Series(index = Series.index)
    
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

def insert_to_db(df: pd.DataFrame):
    """
    Inserts data from the processed DataFrame (df) into the EmailDB table.
    
    It maps:
    - df['sender']       -> EmailDB.sender
    - df['recipient1']   -> EmailDB.receiver (using the first recipient)
    - df['Subject']      -> EmailDB.subject
    - df['text']      -> EmailDB.content 
    """
    print(f"Starting database insertion for {len(df)} records...")
    
    # Get a database session using the generator dependency
    db_generator = get_db()
    db: Session = next(db_generator) 
    
    try:
        new_records = []
        
        # Iterate over DataFrame rows
        for index, row in df.iterrows():
            # NOTE: We assume 'content' column holds the message body 
            # after your initial cleaning (before feature extraction). 
            # If the body is in a different column, adjust 'row['content']'.

            email_record = EmailDB(
                sender=row['sender'],
                receiver=row['recipient1'],  # Using recipient1 as the primary receiver
                subject=row['Subject'],
                content=row['text'],
                sent_at=row['date'],
            )
            new_records.append(email_record)
            if(index%100 == 0):
                print("add")

        
        # Batch insert for efficiency
        db.add_all(new_records)
        db.commit()
        print(f" Successfully inserted {len(new_records)} email records into the database.")
            
    except Exception as e:
        db.rollback()
        print(f" An error occurred during insertion. Transaction rolled back: {e}")
    finally:
        db_generator.close()
        print("Database session closed.")

# 1. Load the data
df = pd.read_csv('backend/emails.csv')
original_rows = len(df)

# 2. Extract the 'text' (message body) first, applying the filter logic inside the function
# Rows identified as non-standard will now have 'text' = NaN
df['text'] = get_message(df.message)

# 3. Filter the DataFrame to KEEP only rows where 'text' is NOT NaN
df_filtered = df[df['text'].notna()].copy()

# Print status before proceeding
filtered_rows = len(df_filtered)
print(f"Original rows: {original_rows}")
print(f"Filtered rows: {filtered_rows}")
print(f"Rows excluded (Non-standard headers): {original_rows - filtered_rows}")

# 4. Extract remaining features ONLY on the clean messages (df_filtered)
df_filtered['sender'], df_filtered['recipient1'], df_filtered['recipient2'], df_filtered['recipient3'] = get_sender_and_receiver(df_filtered.message)
df_filtered['Subject'] = get_subject(df_filtered.message)
df_filtered['folder'] = get_folder(df_filtered.message)
df_filtered['date'] = get_date(df_filtered.message)
# df_filtered['date'] = df_filtered['date'].apply(parsedate_to_datetime)

# 5. Drop original columns
df_filtered = df_filtered.drop(['message', 'file'], axis = 1)

# 6. Filter for the requested sender ('kay.mann@enron.com')
sender = 'kay.mann@enron.com'
extracted_df = df_filtered[df_filtered['sender'].str.strip() == sender]

# 7. Save the final filtered DataFrame
insert_to_db(extracted_df)