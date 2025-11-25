import re
import numpy as np
import pandas as pd
from collections import Counter
def sentence_analysis(email_content: str):
    """
    Analyzes preprocessed emails from a single multi-line string.
    Each email is expected to be on a separate line.
    Calculates sentence and word statistics for stylometry analysis.
    
    Args:
        email_content (str): A single string containing all emails, 
                             separated by newlines.
        
    Returns:
        dict: A dictionary of calculated stylometric statistics, or None.
    """
    
    # Split the single string into a list of emails (lines)
    emails = email_content.splitlines()
    
    all_sentence_lengths = []
    all_word_lengths = []
    email_word_counts = []
    total_commas = 0
    total_words_all_emails = 0
    
    for email_text in emails:
        # Strip leading/trailing whitespace
        email_text = email_text.strip()
        
        # Skip empty lines
        if not email_text:
            continue
        
        # Extract all words from the email
        words = re.findall(r'\b\w+\b', email_text.lower())
        
        # Skip emails with no words
        if not words:
            continue
        
        # Store email length in words
        email_word_counts.append(len(words))
        total_words_all_emails += len(words)
        
        # Store word lengths for word length distribution
        word_lengths = [len(word) for word in words]
        all_word_lengths.extend(word_lengths)
        
        # Count commas in this email
        total_commas += email_text.count(',')
        
        # Split into sentences - handles period, exclamation, and question marks
        sentences = [s.strip() for s in re.split(r'[.!?]+', email_text) if s.strip()]
        
        for sentence in sentences:
            # Extract words from each sentence
            sentence_words = re.findall(r'\b\w+\b', sentence.lower())
            
            # Only count sentences with at least one word
            if sentence_words:
                all_sentence_lengths.append(len(sentence_words))
    
    # --- Calculations ---
    
    # Check if we have valid data
    if not all_sentence_lengths:
        print("No valid sentences found in the input string.")
        return None
    
    if not email_word_counts:
        print("No valid emails found in the input string.")
        return None
    
    # Calculate sentence length statistics
    sent_len_mean = np.mean(all_sentence_lengths)
    sent_len_std = np.std(all_sentence_lengths)
    
    # Calculate word length statistics
    word_len_mean = np.mean(all_word_lengths)
    word_len_std = np.std(all_word_lengths)
    
    # Calculate average email length
    avg_email_length = np.mean(email_word_counts)
    
    # Calculate words per comma
    if total_commas > 0:
        words_per_comma = total_words_all_emails / total_commas
    else:
        words_per_comma = float('inf')
    
    # Create frequency distributions (dataframes removed for brevity, but calculations kept)
    word_len_counts = Counter(all_word_lengths)
    total_words = len(all_word_lengths)
    # ... (word_len_freq_df creation)
    
    sent_len_counts = Counter(all_sentence_lengths)
    total_sentences = len(all_sentence_lengths)
    # ... (sent_len_freq_df creation)
    
    # Return results
    return {
        "sentence_length_mean": sent_len_mean,
        "sentence_length_std": sent_len_std,
        "word_length_mean": word_len_mean,
        "word_length_std": word_len_std,
        "avg_email_length": avg_email_length,
        "words_per_comma": words_per_comma
    }


# --- Example Usage ---
