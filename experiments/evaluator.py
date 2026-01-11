import requests
import json
import re
from typing import Dict, List, Tuple
import argparse

class StyleTransferEvaluator:
    def __init__(self, model_name: str = "ministral-3:8b", base_url: str = "http://localhost:11434"):
        """
        Initialize the evaluator with Ollama configuration.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def _call_ollama(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Call Ollama API with the given prompt.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (lower = more deterministic)
            
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
    
    def _extract_score(self, response: str, scale_type: str = "1-5") -> float:
        """
        Extract numerical score from model response.
        
        Args:
            response: Model's text response
            scale_type: Expected scale format ("1-5" or "0-1")
            
        Returns:
            Extracted score as float, or -1 if extraction failed
        """
        # Look for patterns like "3.5", "4", "0.8", etc.
        patterns = [
            r'\b(\d+\.?\d*)\b',  # Any number
            r'score[:\s]+(\d+\.?\d*)',  # "score: X" or "score X"
            r'rating[:\s]+(\d+\.?\d*)',  # "rating: X"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response.lower())
            if matches:
                try:
                    score = float(matches[0])
                    # Validate score is in expected range
                    if scale_type == "1-5" and 1 <= score <= 5:
                        return score
                    elif scale_type == "0-1" and 0 <= score <= 1:
                        return score
                except ValueError:
                    continue
        
        print(f"Warning: Could not extract valid score from response: {response[:100]}")
        return -1.0
    
    def evaluate_style_transfer(self, original: str, recreated: str) -> Tuple[float, str]:
        """
        Evaluate style transfer between original and recreated text.
        Scale: 1 (completely different styles) to 5 (completely identical styles)
        
        Args:
            original: Original email text
            recreated: Recreated/transferred email text
            
        Returns:
            Tuple of (score, full_response)
        """
        prompt = f"""You are a strict style transfer evaluator. Compare the writing style of these two emails:

    ORIGINAL EMAIL (E1): {original}

    RECREATED EMAIL (E2): {recreated}

    Evaluate how similar the WRITING STYLE is between E1 and E2 on a scale from 1 to 5:
    - 1 = Completely different styles
    - 2 = Mostly different styles with minor similarities
    - 3 = Moderately similar styles with notable differences
    - 4 = Very similar styles with minor differences
    - 5 = Completely identical styles

    Be STRICT in your evaluation. Focus on these specific style features:

    1. **Sentence Structure**: Length, complexity, use of clauses (simple vs. compound vs. complex). World length should be comparable
    2. **Vocabulary Choice**: Formal vs. informal words, technical vs. casual language, word sophistication
    3. **Tone**: Professional, friendly, authoritative, casual, urgent, etc.
    4. **Formality Level**: Greetings, closings, politeness markers, contractions usage
    5. **Punctuation Patterns**: Use of exclamation marks, dashes, semicolons, ellipses
    6. **Paragraph Organization**: Length and structure of paragraphs
    7. **Expressiveness**: Use of adjectives, adverbs, intensifiers, hedging language
    8. **Voice**: Active vs. passive voice preference

    Ignore the content/meaning and focus ONLY on HOW the message is written, not WHAT is being said.

    Provide your answer as a single INTEGER between 1 and 5. Do not use decimals."""

        response = self._call_ollama(prompt)
        score = self._extract_score(response, scale_type="1-5")
        return score, response
    
    def evaluate_content_preservation(self, original: str, recreated: str) -> Tuple[int, str]:
        """
        Evaluate how much content is preserved between original and recreated text.
        Scale: 0 (content not preserved) or 1 (content preserved)
        
        Args:
            original: Original email text
            recreated: Recreated/transferred email text
            
        Returns:
            Tuple of (score, full_response)
        """
        prompt = f"""Here is the original email E1: {original}
    and reconstructed email E2: {recreated}

    Does E2 preserve the main content and topic of E1?

    Answer with ONLY a single digit:
    - 0 if the content is NOT preserved (different topic, missing key information, or significantly altered meaning)
    - 1 if the content IS preserved (same topic and main points, even if wording differs)

    Your answer (0 or 1):"""

        response = self._call_ollama(prompt)
        score = self._extract_binary_score(response)
        return score, response

    def evaluate_naturalness(self, recreated: str) -> Tuple[int, str]:
        """
        Evaluate naturalness/coherence of recreated text.
        Scale: 0 (unnatural/incoherent) or 1 (natural/coherent)
        
        Args:
            recreated: Recreated/transferred email text
            
        Returns:
            Tuple of (score, full_response)
        """
        prompt = f"""Here is a reconstructed email E2: {recreated}

    Is this email natural and coherent?

    Answer with ONLY a single digit:
    - 0 if the email is unnatural, incoherent, or difficult to understand
    - 1 if the email is natural, coherent, and reads well

    Your answer (0 or 1):"""

        response = self._call_ollama(prompt)
        score = self._extract_binary_score(response)
        return score, response

    def _extract_binary_score(self, response: str) -> int:
        """
        Extract a binary score (0 or 1) from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Integer score (0 or 1), defaults to 0 if parsing fails
        """
        # Clean the response
        response = response.strip().lower()
        
        # Try to find 0 or 1 in the response
        import re
        
        # Look for standalone 0 or 1
        match = re.search(r'\b([01])\b', response)
        if match:
            return int(match.group(1))
        
        # Default to 0 if we can't determine
        print(f"Warning: Could not extract binary score from response: {response}")
        return None
    
    def evaluate_all(self, original: str, recreated: str) -> Dict[str, any]:
        """
        Run all three evaluation metrics on the text pair.
        
        Args:
            original: Original email text
            recreated: Recreated/transferred email text
            
        Returns:
            Dictionary containing all scores and responses
        """
        print("Evaluating style transfer...")
        style_score, style_response = self.evaluate_style_transfer(original, recreated)
        
        print("Evaluating content preservation...")
        content_score, content_response = self.evaluate_content_preservation(original, recreated)
        
        print("Evaluating naturalness...")
        natural_score, natural_response = self.evaluate_naturalness(recreated)
        
        return {
            "style_transfer": {
                "score": style_score,
                "response": style_response,
                "description": "1=different styles, 5=Identical styles"
            },
            "content_preservation": {
                "score": content_score,
                "response": content_response,
                "description": "0=different topic, 1=identical topic"
            },
            "naturalness": {
                "score": natural_score,
                "response": natural_response,
                "description": "1=low coherence, 5=highest coherence"
            }
        }
    
    def evaluate_batch(self, email_pairs: List[Tuple[str, str]]) -> List[Dict[str, any]]:
        """
        Evaluate multiple email pairs.
        
        Args:
            email_pairs: List of (original, recreated) tuples
            
        Returns:
            List of evaluation results for each pair
        """
        results = []
        for i, (original, recreated) in enumerate(email_pairs, 1):
            print(f"\n{'='*60}")
            print(f"Evaluating pair {i}/{len(email_pairs)}")
            print(f"{'='*60}")
            result = self.evaluate_all(original, recreated)
            results.append(result)
        return results



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Style Transfer Evaluator")
    parser.add_argument("--model-name", default="ministral-3:8b", help="Model name to use")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Base URL for the API")
    
    args = parser.parse_args()
    
    evaluator = StyleTransferEvaluator(model_name=args.model_name, base_url=args.base_url)   
    
    # Load recreated emails from JSON
    print("Loading recreated_emails.json...")
    with open('experiments/recreated_emails.json', 'r') as f:
        recreated_emails_data = json.load(f)
    
    print(f"Loaded {len(recreated_emails_data)} emails from JSON")
    
    # Prepare email pairs for evaluation
    # Pair 1: (original, recreated_context_only)
    pairs_context_only = []
    # Pair 2: (original, recreated_rag)
    pairs_rag = []
    
    for email_data in recreated_emails_data:
        original = email_data.get('original_content', '')
        recreated_context = email_data.get('recreated_email_context_only', '')
        recreated_rag = email_data.get('recreated_email_rag', '')
        
        if original and recreated_context:
            pairs_context_only.append((original, recreated_context))
        
        if original and recreated_rag:
            pairs_rag.append((original, recreated_rag))
    
    print(f"\nPrepared {len(pairs_context_only)} pairs for context-only evaluation")
    print(f"Prepared {len(pairs_rag)} pairs for RAG evaluation")
    
    # Evaluate context-only recreations
    print("\n" + "="*60)
    print("EVALUATING CONTEXT-ONLY RECREATIONS")
    print("="*60)
    
    results_context_only = evaluator.evaluate_batch(pairs_context_only)
    
    # Evaluate RAG recreations
    print("\n" + "="*60)
    print("EVALUATING RAG RECREATIONS")
    print("="*60)
    
    results_rag = evaluator.evaluate_batch(pairs_rag)
    
    # Calculate average scores for context-only
    print("\n" + "="*60)
    print("CONTEXT-ONLY METHOD - AVERAGE SCORES")
    print("="*60)
    
    valid_context_results = [r for r in results_context_only if r['style_transfer']['score'] != -1]
    if valid_context_results:
        avg_style_context = sum(r['style_transfer']['score'] for r in valid_context_results) / len(valid_context_results)
        avg_content_context = sum(r['content_preservation']['score'] for r in valid_context_results) / len(valid_context_results)
        avg_natural_context = sum(r['naturalness']['score'] for r in valid_context_results) / len(valid_context_results)
        
        print(f"  Style Transfer: {avg_style_context:.2f}/5.0")
        print(f"  Content Preservation: {avg_content_context:.2f}/5.0")
        print(f"  Naturalness: {avg_natural_context:.2f}/5.0")
    
    # Calculate average scores for RAG
    print("\n" + "="*60)
    print("RAG METHOD - AVERAGE SCORES")
    print("="*60)
    
    valid_rag_results = [r for r in results_rag if r['style_transfer']['score'] != -1]
    if valid_rag_results:
        avg_style_rag = sum(r['style_transfer']['score'] for r in valid_rag_results) / len(valid_rag_results)
        avg_content_rag = sum(r['content_preservation']['score'] for r in valid_rag_results) / len(valid_rag_results)
        avg_natural_rag = sum(r['naturalness']['score'] for r in valid_rag_results) / len(valid_rag_results)
        
        print(f"  Style Transfer: {avg_style_rag:.2f}/5.0")
        print(f"  Content Preservation: {avg_content_rag:.2f}/5.0")
        print(f"  Naturalness: {avg_natural_rag:.2f}/5.0")
    
    # Comparison
    print("\n" + "="*60)
    print("COMPARISON: CONTEXT-ONLY vs RAG")
    print("="*60)
    
    if valid_context_results and valid_rag_results:
        print(f"Style Difference:")
        print(f"  Context-only: {avg_style_context:.2f}")
        print(f"  RAG: {avg_style_rag:.2f}")
        print(f"  Difference: {abs(avg_style_context - avg_style_rag):.2f}")
        
        print(f"\nContent Preservation:")
        print(f"  Context-only: {avg_content_context:.2f}")
        print(f"  RAG: {avg_content_rag:.2f}")
        print(f"  Difference: {abs(avg_content_context - avg_content_rag):.2f}")
        
        print(f"\nNaturalness:")
        print(f"  Context-only: {avg_natural_context:.2f}")
        print(f"  RAG: {avg_natural_rag:.2f}")
        print(f"  Difference: {abs(avg_natural_context - avg_natural_rag):.2f}")
    
    # Save evaluation results
    evaluation_results = {
        'context_only': {
            'results': results_context_only,
            'averages': {
                'style_transfer': avg_style_context if valid_context_results else -1,
                'content_preservation': avg_content_context if valid_context_results else -1,
                'naturalness': avg_natural_context if valid_context_results else -1
            }
        },
        'rag': {
            'results': results_rag,
            'averages': {
                'style_transfer': avg_style_rag if valid_rag_results else -1,
                'content_preservation': avg_content_rag if valid_rag_results else -1,
                'naturalness': avg_natural_rag if valid_rag_results else -1
            }
        }
    }
    
    with open('experiments/evaluation_results.json', 'w') as f:
        json.dump(evaluation_results, f, indent=2)
    
    print("\n" + "="*60)
    print("Evaluation results saved to 'evaluation_results.json'")
    print("="*60)