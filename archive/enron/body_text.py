import pandas as pd
import email
from email.parser import Parser
import re
import os

def get_email_info(full_message):
    """Parses a raw email string to extract the sender and body."""
    try:
        # Parse the email string into an EmailMessage object
        msg = Parser().parsestr(full_message)
        
        # Extract sender email address (cleaning up potential extra info like names)
        sender = msg['From']
        if sender:
            # Use a regex to get just the email address
            match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
            sender = match.group(0).lower() if match else sender.lower()
        
        # Extract the body (payload)
        body = msg.get_payload()
        if isinstance(body, list):
            # Simple concatenation if it's a list of parts
            body = ' '.join([part.get_payload() for part in body])
        
        return sender, body
        
    except Exception:
        # Handle parsing errors
        return None, None

def clean_text(text):
    """Basic text preprocessing for stylometry/analysis."""
    if pd.isna(text) or text is None:
        return ""
    
    text = str(text)
    
    # Remove forwarded by sections
    forward_pattern = r'--\s*Forwarded\s*by.*'
    text = re.sub(forward_pattern, '', text, flags=re.IGNORECASE | re.DOTALL)    
    
    # Remove common email artifacts/headers that are sometimes in the body
    text = re.sub(r'(Original Message|-----|From:|To:|Subject:|Sent:|cc:)', '', text, flags=re.IGNORECASE)
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Remove words containing special characters (keep only letters and allowed punctuation: , . ! ?)
    # This regex matches words that contain any character other than letters, spaces, and allowed punctuation
    text = re.sub(r'\b\w*[^\w\s,.!?]\w*\b', '', text)
    
    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_first_n_from_sender(csv_file_path, target_email, max_emails=1000, chunksize=50000):
    """
    Reads the Enron emails CSV in chunks, collects the first 'max_emails'
    sent by the 'target_email', preprocesses them, and saves each email on a separate line.

    Args:
        csv_file_path (str): Path to the 'emails.csv' file.
        target_email (str): The email address to filter by (sender).
        max_emails (int): The maximum number of emails to collect from the sender.
        chunksize (int): The number of rows to read at a time (for efficiency).
    """

    if not os.path.exists(csv_file_path):
        print(f"Error: File not found at {csv_file_path}")
        return

    clean_target_email = target_email.lower().strip()
    collected_bodies = []
    total_rows_read = 0

    print(f"Starting to collect the first {max_emails} emails from {target_email}...")

    # Read the CSV in chunks
    for chunk_df in pd.read_csv(csv_file_path, chunksize=chunksize):
        total_rows_read += len(chunk_df)

        # Parse emails in the current chunk
        parsed_data = chunk_df['message'].apply(lambda x: pd.Series(get_email_info(x), index=['From', 'Body']))
        chunk_df = pd.concat([chunk_df, parsed_data], axis=1)
        
        # Filter for the target email
        sender_emails = chunk_df[chunk_df['From'] == clean_target_email].copy()
        
        # Calculate how many emails we still need
        needed = max_emails - len(collected_bodies)
        
        if needed > 0:
            # Take only what is needed, up to the remaining amount
            emails_to_add = sender_emails.head(needed)
            collected_bodies.extend(emails_to_add['Body'].tolist())
            
            print(f"Emails found in this chunk: {len(emails_to_add)}. Total collected: {len(collected_bodies)}.")
        
        # Check if we have collected the maximum number of emails
        if len(collected_bodies) >= max_emails:
            print(f"Reached the target of {max_emails} emails. Stopping early.")
            break

    if not collected_bodies:
        print(f"No emails found sent by: {target_email} after reading {total_rows_read} rows.")
        return

    # Preprocess the collected bodies
    print(f"Preprocessing {len(collected_bodies)} collected email bodies...")
    preprocessed_bodies = [clean_text(body) for body in collected_bodies]

    # Save each email on a separate line (one email per line)
    output_filename = f"{clean_target_email.replace('@', '-at-').replace('.', '-')}-combined.txt"
    with open(output_filename, 'w', encoding='utf-8') as f:
        for body in preprocessed_bodies:
            # Write each email on one line, skip empty emails
            if body.strip():
                # Replace any newlines within the email body with spaces
                # This ensures each email is truly on one line
                body_single_line = body.replace('\n', ' ').replace('\r', ' ')
                f.write(body_single_line + '\n')

    print(f"\nSuccessfully processed and saved {len(preprocessed_bodies)} emails to: {output_filename}")
    print(f"Each email is stored on a separate line.")


# --- Example Usage ---
# NOTE: Replace with the actual path to your enron emails.csv file
CSV_PATH = 'emails.csv'

# NOTE: Replace with the email address you want to analyze
TARGET_SENDER = 'kay.mann@enron.com' 

# Call the function to get the first 1000 emails from the target sender
preprocess_first_n_from_sender(CSV_PATH, TARGET_SENDER, max_emails=1000)