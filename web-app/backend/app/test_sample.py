import pandas as pd
from email import policy
from email.parser import Parser

def get_email_body(raw_email_text):
    """Extract just the body from raw email"""
    if pd.isna(raw_email_text):
        return None
    
    try:
        parser = Parser(policy=policy.default)
        email_msg = parser.parsestr(raw_email_text)
        
        # Extract body
        if email_msg.is_multipart():
            text_parts = []
            for part in email_msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        text_parts.append(part.get_content())
                    except:
                        pass
            return '\n\n'.join(text_parts)
        else:
            try:
                return email_msg.get_content()
            except:
                payload = email_msg.get_payload(decode=True)
                if payload:
                    try:
                        return payload.decode('utf-8', errors='ignore')
                    except:
                        return str(payload)
    except:
        return None

def show_random_bodies(csv_path='backend/emails.csv', num_samples=10, seed=42, output_file='email_bodies.txt'):
    """Show only the bodies of random emails and save to file"""
    
    df = pd.read_csv(csv_path)
    sample_df = df.sample(n=num_samples, random_state=seed)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, (_, row) in enumerate(sample_df.iterrows(), 1):
            header = f"\n{'='*80}\nEMAIL BODY #{idx}\n{'='*80}\n\n"
            
            print(header)
            f.write(header)
            
            body = get_email_body(row['message'])
            
            if body:
                print(body)
                f.write(body)
            else:
                print("[Failed to extract body]")
                f.write("[Failed to extract body]")
            
            print("\n")
            f.write("\n\n")
    
    print(f"\nEmail bodies saved to: {output_file}")

if __name__ == "__main__":
    show_random_bodies(
        csv_path='app/emails.csv',
        num_samples=10,
        seed=42
    )