import requests
from sqlalchemy.orm import Session
from typing import Dict, List
from .stylometric_features import get_historical_context
from .database import SessionLocal


class EmailRecreator:
    def __init__(self, model_name: str = "ministral-3:8b", base_url: str = "http://localhost:11434"):
        """
        Initialize the email recreator with Ollama configuration.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def _call_ollama(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Call Ollama API with the given prompt.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (higher for more creative outputs)
            
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
    
    def recreate_email_with_context_only(self, result: Dict) -> str:
        """
        Recreate an email using only the context, sender, and receiver.
        
        Args:
            result: Dictionary containing 'context', 'sender', 'receiver', and other fields
            
        Returns:
            Recreated email text
        """
        context = result.get('extracted_context', result.get('context', ''))
        sender = result.get('sender', 'Unknown')
        receiver = result.get('receiver', 'Unknown')
        
        prompt = f"""You are tasked with writing an email based on the following information:

Context: {context}
From: {sender}
To: {receiver}

Write a professional email that fulfills the intent described in the context. The email should sound natural and appropriate for the sender and receiver. Include a proper greeting, body, and closing.

Email:"""

        recreated_email = self._call_ollama(prompt)
        return recreated_email
    
    def recreate_email_with_rag(self, db: Session, result: Dict, number_of_emails: int = 5) -> str:
        """
        Recreate an email using context + RAG (historical emails from sender to receiver).
        
        Args:
            db: SQLAlchemy database session
            result: Dictionary containing 'context', 'sender', 'receiver', and other fields
            number_of_emails: Number of recent emails to retrieve for RAG
            
        Returns:
            Recreated email text
        """
        context = result.get('extracted_context', result.get('context', ''))
        sender = result.get('sender', 'Unknown')
        receiver = result.get('receiver', 'Unknown')
        
        # Get historical context using RAG
        all_emails_context, recent_emails_context = get_historical_context(
            db=db,
            sender=sender,
            receiver=receiver,
            number_of_emails=number_of_emails
        )
        
        # Use recent emails for the prompt (more relevant)
        historical_context = recent_emails_context if recent_emails_context else all_emails_context
        
        prompt = f"""You are tasked with writing an email based on the following information:

Context: {context}
From: {sender}
To: {receiver}

Here are some recent emails from {sender} to {receiver} for reference on writing style and tone:

---RECENT EMAILS---
{historical_context}
---END RECENT EMAILS---

Based on the context and the writing style shown in the recent emails above, write an email that:
1. Fulfills the intent described in the context
2. Matches the writing style, tone, and formality level of the sender's previous emails
3. Sounds natural and consistent with how {sender} typically writes to {receiver}

Include a proper greeting, body, and closing.
Make sure to base you generation on the Recent emails to check see how the message body is. 
is
Email:"""

        recreated_email = self._call_ollama(prompt)
        return recreated_email
    
    def recreate_batch_with_context_only(self, results: List[Dict]) -> List[Dict]:
        """
        Recreate multiple emails using only context.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            List of results with added 'recreated_email_context_only' field
        """
        recreated_results = []
        
        for i, result in enumerate(results, 1):
            print(f"Recreating email {i}/{len(results)} (context only)...", end='\r')
            
            recreated_email = self.recreate_email_with_context_only(result)
            
            # Add recreated email to result
            result_copy = result.copy()
            result_copy['recreated_email_context_only'] = recreated_email
            recreated_results.append(result_copy)
        
        print(f"\nCompleted recreating {len(results)} emails (context only)")
        return recreated_results
    
    def recreate_batch_with_rag(self, db: Session, results: List[Dict], 
                                number_of_emails: int = 5) -> List[Dict]:
        """
        Recreate multiple emails using context + RAG.
        
        Args:
            db: SQLAlchemy database session
            results: List of result dictionaries
            number_of_emails: Number of recent emails to retrieve for each RAG query
            
        Returns:
            List of results with added 'recreated_email_rag' field
        """
        recreated_results = []
        
        for i, result in enumerate(results, 1):
            print(f"Recreating email {i}/{len(results)} (with RAG)...", end='\r')
            
            recreated_email = self.recreate_email_with_rag(db, result, number_of_emails)
            
            # Add recreated email to result
            result_copy = result.copy()
            result_copy['recreated_email_rag'] = recreated_email
            recreated_results.append(result_copy)
        
        print(f"\nCompleted recreating {len(results)} emails (with RAG)")
        return recreated_results
    
    def recreate_batch_both_methods(self, db: Session, results: List[Dict],
                                    number_of_emails: int = 5) -> List[Dict]:
        """
        Recreate emails using both methods (context only and RAG).
        
        Args:
            db: SQLAlchemy database session
            results: List of result dictionaries
            number_of_emails: Number of recent emails to retrieve for RAG
            
        Returns:
            List of results with both 'recreated_email_context_only' and 'recreated_email_rag' fields
        """
        recreated_results = []
        
        for i, result in enumerate(results, 1):
            print(f"Recreating email {i}/{len(results)}...")
            
            # Method 1: Context only
            recreated_context_only = self.recreate_email_with_context_only(result)
            
            # Method 2: Context + RAG
            recreated_rag = self.recreate_email_with_rag(db, result, number_of_emails)
            
            # Add both recreated emails to result
            result_copy = result.copy()
            result_copy['recreated_email_context_only'] = recreated_context_only
            result_copy['recreated_email_rag'] = recreated_rag
            recreated_results.append(result_copy)
            
            print(f"  ✓ Email {i} recreated with both methods")
        
        print(f"\nCompleted recreating {len(results)} emails with both methods")
        return recreated_results

