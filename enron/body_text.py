import pandas as pd
import re

# Load CSV
df = pd.read_csv("emails.csv")

# Extract sender
df['sender'] = df['message'].str.extract(r'From:\s*([^\n\r]+)')

# Filter messages sent by Kay Mann
kay_messages = df[df['sender'] == 'kay.mann@enron.com']

# Extract "To" and "Subject" lines
kay_messages['to'] = kay_messages['message'].str.extract(r'To:\s*([^\n\r]+)')
kay_messages['subject'] = kay_messages['message'].str.extract(r'Subject:\s*([^\n\r]*)')

# Extract body text (everything after the last header line, usually X-FileName)
def extract_body(msg):
    # Split by lines and find the first empty line after headers
    parts = msg.split('\n')
    try:
        empty_idx = next(i for i, line in enumerate(parts) if line.strip() == '')
        body = '\n'.join(parts[empty_idx+1:])
        return body.strip()
    except StopIteration:
        return ''  # return empty if no body found

kay_messages['body'] = kay_messages['message'].apply(extract_body)

# Display first 3 messages with To, Subject, and Body
for i, row in kay_messages.head(3).iterrows():
    print(f"--- Message {i} ---")
    print(f"To: {row['to']}")
    print(f"Subject: {row['subject']}")
    print(f"Body:\n{row['body']}\n")
