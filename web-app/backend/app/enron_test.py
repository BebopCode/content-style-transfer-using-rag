import pandas as pd
import numpy as np
from email import policy
from email.parser import Parser
from email.utils import parsedate_to_datetime
import re
from datetime import datetime
from typing import List, Dict, Optional

def parse_email_headers(raw_email_text):
    """Parse email using Python's email library"""
    if pd.isna(raw_email_text):
        return None
    
    try:
        parser = Parser(policy=policy.default)
        email_msg = parser.parsestr(raw_email_text)
        
        parsed = {
            'from': email_msg.get('From', ''),
            'to': email_msg.get('To', ''),
            'cc': email_msg.get('X-cc', ''),
            'bcc': email_msg.get('X-bcc', ''),
            'subject': email_msg.get('Subject', ''),
            'date_str': email_msg.get('Date', ''),
            'folder': email_msg.get('X-Folder', ''),
            'message_id': email_msg.get('Message-ID', ''),
            'body': ''
        }
        
        # Extract body
        if email_msg.is_multipart():
            text_parts = []
            for part in email_msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        text_parts.append(part.get_content())
                    except:
                        pass
            parsed['body'] = '\n\n'.join(text_parts)
        else:
            try:
                parsed['body'] = email_msg.get_content()
            except:
                payload = email_msg.get_payload(decode=True)
                if payload:
                    try:
                        parsed['body'] = payload.decode('utf-8', errors='ignore')
                    except:
                        parsed['body'] = str(payload)
        
        # Parse date
        if parsed['date_str']:
            try:
                parsed['date'] = parsedate_to_datetime(parsed['date_str'])
            except:
                parsed['date'] = None
        else:
            parsed['date'] = None
        
        return parsed
        
    except Exception as e:
        print(f"Error parsing email: {e}")
        return None

def extract_thread_messages(body: str) -> List[Dict]:
    """
    Extract individual messages from an email thread.
    
    Returns a list of message dictionaries, ordered from newest to oldest.
    Each dict contains: content, from, to, cc, subject, date, is_original
    """
    if not body:
        return []
    
    messages = []
    lines = body.split('\n')
    
    # Pattern to detect embedded email headers
    # Look for patterns like "From: xxx" followed by "To:" and optionally other headers
    embedded_header_pattern = re.compile(
        r'^\s*From:\s*(.+?)(?:\s+on\s+(.+?))?\s*$',
        re.IGNORECASE
    )
    
    current_message = {
        'content': [],
        'from': None,
        'to': None,
        'cc': None,
        'subject': None,
        'date': None,
        'is_original': True
    }
    
    in_embedded_message = False
    embedded_message = {
        'content': [],
        'from': None,
        'to': None,
        'cc': None,
        'subject': None,
        'date': None,
        'is_original': False
    }
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for "-----Original Message-----" separator
        if '-----Original Message-----' in line:
            # Save current message if it has content
            if current_message['content']:
                messages.append({
                    'content': '\n'.join(current_message['content']).strip(),
                    'from': current_message['from'],
                    'to': current_message['to'],
                    'cc': current_message['cc'],
                    'subject': current_message['subject'],
                    'date': current_message['date'],
                    'is_original': current_message['is_original']
                })
            
            # Start new embedded message
            current_message = {
                'content': [],
                'from': None,
                'to': None,
                'cc': None,
                'subject': None,
                'date': None,
                'is_original': False
            }
            in_embedded_message = True
            i += 1
            continue
        
        # Check for embedded email header block (From: ... To: ... pattern)
        from_match = re.match(r'^\s*From:\s*(.+)', line, re.IGNORECASE)
        if from_match and i + 1 < len(lines):
            # Check if next line is "To:" or "Sent:" - indicates embedded email
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            
            if re.match(r'^\s*(To|Sent):\s*', next_line, re.IGNORECASE):
                # This is an embedded email header
                
                # Save current message if it has content
                if current_message['content']:
                    messages.append({
                        'content': '\n'.join(current_message['content']).strip(),
                        'from': current_message['from'],
                        'to': current_message['to'],
                        'cc': current_message['cc'],
                        'subject': current_message['subject'],
                        'date': current_message['date'],
                        'is_original': current_message['is_original']
                    })
                
                # Parse embedded headers
                embedded_headers = {}
                embedded_headers['from'] = from_match.group(1).strip()
                
                # Parse the next few lines for headers
                j = i + 1
                while j < len(lines) and j < i + 10:  # Look ahead max 10 lines
                    header_line = lines[j]
                    
                    if re.match(r'^\s*To:\s*(.+)', header_line, re.IGNORECASE):
                        embedded_headers['to'] = re.match(r'^\s*To:\s*(.+)', header_line, re.IGNORECASE).group(1).strip()
                    elif re.match(r'^\s*(cc|Cc):\s*(.+)', header_line, re.IGNORECASE):
                        embedded_headers['cc'] = re.match(r'^\s*(cc|Cc):\s*(.+)', header_line, re.IGNORECASE).group(2).strip()
                    elif re.match(r'^\s*Subject:\s*(.+)', header_line, re.IGNORECASE):
                        embedded_headers['subject'] = re.match(r'^\s*Subject:\s*(.+)', header_line, re.IGNORECASE).group(1).strip()
                    elif re.match(r'^\s*(Sent|Date):\s*(.+)', header_line, re.IGNORECASE):
                        embedded_headers['date'] = re.match(r'^\s*(Sent|Date):\s*(.+)', header_line, re.IGNORECASE).group(2).strip()
                    elif header_line.strip() == '' or not re.match(r'^\s*\w+:', header_line):
                        # End of headers
                        break
                    
                    j += 1
                
                # Start new message with these headers
                current_message = {
                    'content': [],
                    'from': embedded_headers.get('from'),
                    'to': embedded_headers.get('to'),
                    'cc': embedded_headers.get('cc'),
                    'subject': embedded_headers.get('subject'),
                    'date': embedded_headers.get('date'),
                    'is_original': False
                }
                
                i = j  # Skip past the headers we just processed
                continue
        
        # Regular content line
        # Skip quote markers (lines starting with >)
        if not line.strip().startswith('>'):
            current_message['content'].append(line)
        
        i += 1
    
    # Don't forget the last message
    if current_message['content']:
        messages.append({
            'content': '\n'.join(current_message['content']).strip(),
            'from': current_message['from'],
            'to': current_message['to'],
            'cc': current_message['cc'],
            'subject': current_message['subject'],
            'date': current_message['date'],
            'is_original': current_message['is_original']
        })
    
    return messages

def process_emails_to_database_format(csv_path='backend/emails.csv', output_csv='emails_flattened.csv'):
    """
    Process emails and flatten threads into individual messages for database insertion
    """
    print(f"Loading emails from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Total emails: {len(df)}")
    
    flattened_records = []
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"Processing email {idx}/{len(df)}...")
        
        # Parse the main email
        parsed = parse_email_headers(row['message'])
        
        if not parsed:
            continue
        
        # Extract thread messages from body
        thread_messages = extract_thread_messages(parsed['body'])
        
        if not thread_messages:
            # No thread detected, treat entire body as single message
            thread_messages = [{
                'content': parsed['body'],
                'from': None,
                'to': None,
                'cc': None,
                'subject': None,
                'date': None,
                'is_original': True
            }]
        
        # Create database records
        # The first message uses the main email headers
        for msg_idx, thread_msg in enumerate(thread_messages):
            record = {
                'original_email_id': idx,  # Link back to original email
                'thread_position': msg_idx,  # 0 = most recent, higher = older
                'is_original_content': thread_msg['is_original'] if msg_idx == 0 else False,
                'sender': thread_msg['from'] if thread_msg['from'] else parsed['from'],
                'receiver': thread_msg['to'] if thread_msg['to'] else parsed['to'],
                'cc': thread_msg['cc'] if thread_msg['cc'] else parsed['cc'],
                'bcc': parsed['bcc'] if msg_idx == 0 else None,
                'subject': thread_msg['subject'] if thread_msg['subject'] else parsed['subject'],
                'date': thread_msg['date'] if thread_msg['date'] else parsed['date_str'],
                'folder': parsed['folder'] if msg_idx == 0 else None,
                'message_id': parsed['message_id'] if msg_idx == 0 else None,
                'content': thread_msg['content'],
                'content_length': len(thread_msg['content']),
                'is_reply': msg_idx > 0,  # True if this is a reply in the thread
                'has_replies': len(thread_messages) > 1 if msg_idx == 0 else False
            }
            
            flattened_records.append(record)
    
    # Create DataFrame
    result_df = pd.DataFrame(flattened_records)
    
    print(f"\nProcessing complete!")
    print(f"Original emails: {len(df)}")
    print(f"Total individual messages extracted: {len(result_df)}")
    print(f"Original content messages: {result_df['is_original_content'].sum()}")
    print(f"Reply messages: {result_df['is_reply'].sum()}")
    
    # Save to CSV
    result_df.to_csv(output_csv, index=False)
    print(f"\nFlattened emails saved to: {output_csv}")
    
    # Show sample
    print("\n" + "="*80)
    print("SAMPLE RECORDS:")
    print("="*80)
    
    # Show first email with replies
    sample_email_id = result_df[result_df['has_replies'] == True]['original_email_id'].iloc[0] if len(result_df[result_df['has_replies'] == True]) > 0 else 0
    sample_records = result_df[result_df['original_email_id'] == sample_email_id]
    
    for _, record in sample_records.iterrows():
        print(f"\nThread Position: {record['thread_position']}")
        print(f"From: {record['sender']}")
        print(f"To: {record['receiver']}")
        print(f"Subject: {record['subject']}")
        print(f"Is Original Content: {record['is_original_content']}")
        print(f"Is Reply: {record['is_reply']}")
        print(f"Content ({record['content_length']} chars):")
        print(record['content'][:300])
        print("...")
        print("-" * 80)
    
    return result_df

def inspect_sample_threads(csv_path='backend/emails.csv', num_samples=10):
    """
    Inspect sample emails to see thread extraction in action
    """
    print(f"Loading sample emails from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Get samples
    sample_df = df.sample(n=num_samples, random_state=42)
    
    for idx, (_, row) in enumerate(sample_df.iterrows(), 1):
        print(f"\n{'='*80}")
        print(f"EMAIL #{idx}")
        print(f"{'='*80}")
        
        parsed = parse_email_headers(row['message'])
        if not parsed:
            print("Failed to parse")
            continue
        
        print(f"From: {parsed['from']}")
        print(f"To: {parsed['to']}")
        print(f"Subject: {parsed['subject']}")
        print(f"Date: {parsed['date_str']}")
        
        # Extract thread messages
        thread_messages = extract_thread_messages(parsed['body'])
        
        print(f"\nThread contains {len(thread_messages)} message(s)")
        
        for msg_idx, msg in enumerate(thread_messages):
            print(f"\n--- MESSAGE {msg_idx + 1} ---")
            print(f"From: {msg['from'] or '(from main header)'}")
            print(f"To: {msg['to'] or '(from main header)'}")
            print(f"Is Original: {msg['is_original']}")
            print(f"Content length: {len(msg['content'])} chars")
            print(f"Content preview:")
            print(msg['content'][:400])
            if len(msg['content']) > 400:
                print("...")

if __name__ == "__main__":
    # First, inspect some samples to see how thread extraction works
    print("Step 1: Inspecting sample emails to demonstrate thread extraction\n")
    inspect_sample_threads(csv_path='app/emails.csv', num_samples=5)
    
    print("\n\n" + "="*80)
    print("Step 2: Processing all emails and creating flattened database format")
    print("="*80 + "\n")
    
    # Process all emails
    result_df = process_emails_to_database_format(
        csv_path='app/emails.csv',
        output_csv='emails_flattened.csv'
    )