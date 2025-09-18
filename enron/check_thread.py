import pandas as pd
import email
from collections import Counter

def get_all_header_names(df):
    """
    Extract all unique header names from all emails in the dataset.
    
    Args:
        df: DataFrame containing emails
        
    Returns:
        dict: Header names with their frequency counts
    """
    
    # Try to find the message column
    message_column = None
    possible_columns = ['message', 'content', 'body', 'text', 'email', 'mail']
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in possible_columns):
            message_column = col
            break
    
    if message_column is None:
        print("Available columns:", list(df.columns))
        message_column = input("Enter the column name that contains email content: ")
    
    print(f"Using column: '{message_column}'")
    
    # Counter to track header frequencies
    header_counter = Counter()
    processed_emails = 0
    errors = 0
    
    # Process each email
    for idx, row in df.iterrows():
        try:
            message_content = row[message_column]
            
            # Skip null/empty messages
            if pd.isna(message_content):
                continue
                
            # Parse the email
            email_obj = email.message_from_string(str(message_content))
            
            # Extract all header names
            for header_name in email_obj.keys():
                header_counter[header_name] += 1
            
            processed_emails += 1
            
        except Exception as e:
            errors += 1
            if errors <= 3:  # Show first few errors
                print(f"Error processing email {idx}: {e}")
    
    print(f"\nProcessed {processed_emails} emails successfully")
    print(f"Encountered {errors} errors")
    
    return dict(header_counter)

# Main execution
try:
    # Load the CSV file
    df = pd.read_csv('emails.csv')
    print(f"Loaded {len(df)} emails from CSV")
    
    # Get all header names
    headers = get_all_header_names(df)
    
    # Display results
    print(f"\n=== FOUND {len(headers)} UNIQUE HEADER NAMES ===")
    
    # Sort headers by frequency (most common first)
    sorted_headers = sorted(headers.items(), key=lambda x: x[1], reverse=True)
    
    for header_name, count in sorted_headers:
        percentage = (count / len(df)) * 100
        print(f"{header_name}: {count} emails ({percentage:.1f}%)")
    
    print(f"\n=== HEADER NAMES ONLY (alphabetical) ===")
    header_names_only = sorted(headers.keys())
    for header in header_names_only:
        print(header)

except FileNotFoundError:
    print("Error: 'emails.csv' not found")
except Exception as e:
    print(f"Error: {e}")