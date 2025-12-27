import requests
import json
from typing import Dict

class EmailContextExtractor:
    def __init__(self, model_name: str = "ministral-3:8b", base_url: str = "http://localhost:11434"):
        """
        Initialize the context extractor with Ollama configuration.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def _call_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        """
        Call Ollama API with the given prompt.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature
            
        Returns:
            Model's response text
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {e}")
            return ""
    
    def extract_context(self, email: str) -> Dict[str, str]:
        """
        Extract context from an email.
        
        Args:
            email: The original email text
            
        Returns:
            Dictionary containing 'context' and 'word_count'
        """
        prompt = f"""Analyze the following email and provide a concise summary of its intent and who it is addressed to.

Email:
{email}

Provide a summary in MAXIMUM 50 words. Keep it under 50 words total."""

        response = self._call_ollama(prompt)
        
        # Ensure context is under 50 words
        words = response.split()
        if len(words) > 50:
            context = ' '.join(words[:50]) + '...'
        else:
            context = response
        
        return {
            'context': context,
            'word_count': len(context.split())
        }
    
    def extract_context_batch(self, emails: list) -> list:
        """
        Extract context from multiple emails.
        
        Args:
            emails: List of email texts
            
        Returns:
            List of context dictionaries
        """
        results = []
        for i, email in enumerate(emails, 1):
            print(f"Processing email {i}/{len(emails)}...")
            context_info = self.extract_context(email)
            results.append(context_info)
        return results


# Example usage
if __name__ == "__main__":
    # Initialize extractor
    extractor = EmailContextExtractor(model_name="ministral-3:8b")
    
    # Example emails
    example_email_1 = """Hi John,
    
I hope this email finds you well. I wanted to reach out regarding the quarterly report that was due last Friday. Could you please provide an update on the status? We need to finalize the numbers before the board meeting next week.

Best regards,
Sarah"""
    
    example_email_2 = """Dear Team,
    
This is to remind everyone about the mandatory safety training scheduled for tomorrow at 2 PM in Conference Room B. Please bring your employee ID badges and be prepared to take notes.

Thanks,
HR Department"""
    
    example_email_3 = """Hey Mike,

Thanks for your proposal! I reviewed it over the weekend and I think it's great. Let's schedule a call this week to discuss the implementation timeline and budget allocation.

Cheers,
Emma"""
    
    # Single email extraction
    print("=" * 60)
    print("Single Email Context Extraction")
    print("=" * 60)
    
    context_info = extractor.extract_context(example_email_1)
    
    print(f"\nOriginal Email:")
    print(f"{example_email_1}\n")
    print(f"Extracted Context ({context_info['word_count']} words):")
    print(f"{context_info['context']}")
    
    # Batch extraction
    print("\n" + "=" * 60)
    print("Batch Email Context Extraction")
    print("=" * 60)
    
    emails = [example_email_1, example_email_2, example_email_3]
    batch_results = extractor.extract_context_batch(emails)
    
    for i, result in enumerate(batch_results, 1):
        print(f"\nEmail {i}:")
        print(f"Context ({result['word_count']} words): {result['context']}")
        print("-" * 60)
    
    # Save results to file (optional)
    print("\n" + "=" * 60)
    print("Saving results to JSON...")
    
    output_data = {
        'emails': emails,
        'contexts': batch_results
    }
    
    with open('email_contexts.json', 'w') as f:
        json.dump(output_data, indent=2, fp=f)
    
    print("Results saved to 'email_contexts.json'")