from sqlalchemy.orm import Session
from typing import List, Dict
import json
from datetime import datetime
from .context_extractor import EmailContextExtractor
from .models import EmailDB
from .database import SessionLocal
from .email_recreator import EmailRecreator
from sqlalchemy import func

def sample_emails_by_sender(db: Session, sender: str, limit: int = 100) -> List[EmailDB]:
    """
    Randomly sample emails from a specific sender.
    
    Args:
        db: SQLAlchemy database session
        sender: Email address or identifier of the sender
        limit: Maximum number of emails to retrieve (default: 100)
    
    Returns:
        List of EmailDB objects (randomly sampled)
    """
    emails = db.query(EmailDB).filter(
        EmailDB.sender == sender
    ).order_by(func.random()).limit(limit).all()
    
    return emails


def extract_contexts_for_sender(sender: str, limit: int = 100, 
                                model_name: str = "ministral-3:8b",
                                save_to_file: bool = True,
                                output_file: str = None) -> List[Dict]:
    """
    Pipeline to sample emails from a sender and extract context for each.
    
    Args:
        sender: Email address or identifier of the sender
        limit: Number of emails to sample (default: 100)
        model_name: Ollama model to use for extraction
        save_to_file: Whether to save results to JSON file
        output_file: Custom output filename (optional)
    
    Returns:
        List of dictionaries containing email info and extracted context
    """
    # Initialize database session
    db = SessionLocal()
    
    try:
        # Sample emails
        print(f"Sampling up to {limit} emails from sender: {sender}")
        emails = sample_emails_by_sender(db, sender, limit)
        
        if not emails:
            print(f"No emails found for sender: {sender}")
            return []
        
        print(f"Found {len(emails)} emails. Extracting contexts...")
        
        # Initialize context extractor
        extractor = EmailContextExtractor(model_name=model_name)
        
        # Extract context for each email
        results = []
        for i, email in enumerate(emails, 1):
            print(f"Processing email {i}/{len(emails)}...", end='\r')
            
            # Extract context
            context_info = extractor.extract_context(email.content)
            
            # Combine email metadata with context
            result = {
                'email_id': email.id if hasattr(email, 'id') else None,
                'sender': email.sender,
                'receiver': email.receiver,
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'subject': email.subject if hasattr(email, 'subject') else None,
                'original_content': email.content,
                'extracted_context': context_info['context'],
                'context_word_count': context_info['word_count']
            }
            
            results.append(result)
        
        print(f"\nSuccessfully extracted contexts for {len(results)} emails")
        
        # Save to file if requested
        if save_to_file:
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"email_contexts_{sender.replace('@', '_')}_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"Results saved to: {output_file}")
        
        return results
        
    finally:
        # Close database session
        db.close()


def extract_contexts_batch(senders: List[str], limit_per_sender: int = 100,
                          model_name: str = "ministral-3:8b") -> Dict[str, List[Dict]]:
    """
    Extract contexts for multiple senders.
    
    Args:
        senders: List of sender email addresses
        limit_per_sender: Maximum emails per sender
        model_name: Ollama model to use
    
    Returns:
        Dictionary mapping sender to their extracted contexts
    """
    all_results = {}
    
    for sender in senders:
        print(f"\n{'='*60}")
        print(f"Processing sender: {sender}")
        print(f"{'='*60}")
        
        results = extract_contexts_for_sender(
            sender=sender,
            limit=limit_per_sender,
            model_name=model_name,
            save_to_file=True
        )
        
        all_results[sender] = results
    
    return all_results


def print_summary(results: List[Dict]):
    """
    Print a summary of extracted contexts.
    
    Args:
        results: List of result dictionaries
    """
    if not results:
        print("No results to summarize")
        return
    
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total emails processed: {len(results)}")
    
    # Calculate statistics
    avg_word_count = sum(r['context_word_count'] for r in results) / len(results)
    
    print(f"Average context word count: {avg_word_count:.1f}")
    
    # Show some examples
    print("\n" + "="*60)
    print("EXAMPLE EXTRACTIONS (First 3)")
    print("="*60)
    
    for i, result in enumerate(results[:10], 1):
        print(f"\nEmail {i}:")
        print(f"  Sender: {result['sender']}")
        print(f"  Receiver: {result['receiver']}")
        print(f"  Sent: {result['sent_at']}")
        print(f"  Context: {result['extracted_context']}")
        print("-" * 60)


# Main execution
if __name__ == "__main__":
    # Example usage: Extract contexts for a single sender
    sender_email = "vince.kaminski@enron.com"
    
    print("Starting Email Context Extraction Pipeline")
    print("="*60)
    
    # Run extraction
    results = extract_contexts_for_sender(
        sender=sender_email,
        limit=10,
        model_name="ministral-3:8b",
        save_to_file=True
    )
    
    
    print("\n" + "="*60)
    print("Starting Email Recreation")
    print("="*60)
    
    recreator = EmailRecreator(model_name="ministral-3:8b")
    db = SessionLocal()
    
    try:
        # Recreate all emails with both methods
        recreated_results = recreator.recreate_batch_both_methods(
            db=db,
            results=results,
            number_of_emails=5
        )
        
        # Save recreated results
        with open('experiments/recreated_emails.json', 'w') as f:
            json.dump(recreated_results, f, indent=2)
        
        print(f"\nRecreated emails saved to 'recreated_emails.json'")
        
    finally:
        db.close()
    
    print("\nPipeline completed!")
    # Print summary
    print_summary(results)
    
    # Example: Process multiple senders
    # senders = ["john@example.com", "sarah@example.com", "mike@example.com"]
    # batch_results = extract_contexts_batch(senders, limit_per_sender=100)
    
    print("\nPipeline completed!")