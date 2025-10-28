import re
import string
import numpy as np
import pandas as pd
from collections import Counter

def analyze_stylometry(file_path):
    """
    Performs word length frequency and sentence length frequency distribution 
    analysis, using the period (.) as the sentence delimiter.
    
    Args:
        file_path (str): The path to the text file to analyze.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    if not text.strip():
        print("Error: The file is empty or contains only whitespace.")
        return
    
    # --- Word Tokenization and Length Analysis ---
    words = re.findall(r'\b\w+\b', text.lower()) 
    word_lengths = [len(word) for word in words if word]
    
    if not word_lengths:
        print("No valid words found in the text.")
        return

    # Word Length Frequency Distribution
    word_len_counts = Counter(word_lengths)
    total_words = len(word_lengths)
    
    word_len_freq_df = pd.DataFrame(word_len_counts.items(), columns=['Word Length (Chars)', 'Count'])
    word_len_freq_df['Frequency (%)'] = (word_len_freq_df['Count'] / total_words) * 100
    word_len_freq_df = word_len_freq_df.sort_values(by='Word Length (Chars)').reset_index(drop=True)

    # Word Length Statistics
    word_len_std = np.std(word_lengths)
    word_len_mean = np.mean(word_lengths)

    # --- Sentence Length Analysis (using '.') ---
    
    # Split text into sentences using a period followed by one or more whitespace characters.
    sentences = [s.strip() for s in re.split(r'\.\s+', text) if s.strip()]
    
    # Calculate sentence length (in words) for each sentence
    sentence_lengths = []
    for sentence in sentences:
        word_list = re.findall(r'\b\w+\b', sentence.lower())
        if word_list:
             sentence_lengths.append(len(word_list))
    
    if not sentence_lengths:
        print("No valid sentences found for analysis based on period delimiter.")
        return

    # Sentence Length Frequency Distribution
    sent_len_counts = Counter(sentence_lengths)
    total_sentences = len(sentence_lengths)

    sent_len_freq_df = pd.DataFrame(sent_len_counts.items(), columns=['Sentence Length (Words)', 'Count'])
    sent_len_freq_df['Frequency (%)'] = (sent_len_freq_df['Count'] / total_sentences) * 100
    sent_len_freq_df = sent_len_freq_df.sort_values(by='Sentence Length (Words)').reset_index(drop=True)

    # Sentence Length Statistics
    sent_len_std = np.std(sentence_lengths)
    sent_len_mean = np.mean(sentence_lengths)

    # --- Output ---
    
    print(f"\n--- Stylometric Analysis of File: {file_path} (Period Delimiter) ---")
    
    # 1. Word Length Results
    print("\n--- Word Length Analysis (Statistics) ---")
    print(f"Total Words Analyzed: {total_words}")
    print(f"Mean Word Length (Characters): {word_len_mean:.2f}")
    print(f"Standard Deviation of Word Length (Characters): {word_len_std:.2f}")
    
    print("\n--- Word Length Frequency Distribution ---")
    print(word_len_freq_df.to_string(index=False))

    # 2. Sentence Length Results
    print("\n--- Sentence Length Analysis (Statistics) ---")
    print(f"Total Sentences Analyzed: {total_sentences}")
    print(f"Mean Sentence Length (Words): {sent_len_mean:.2f}")
    print(f"Standard Deviation of Sentence Length (Words): {sent_len_std:.2f}")
    
    print("\n--- Sentence Length Frequency Distribution ---")
    print(sent_len_freq_df.to_string(index=False))

# --- How to run the analysis ---
# FILE_TO_ANALYZE = 'your_combined_text_file_name.txt' 
# analyze_stylometry_periods(FILE_TO_ANALYZE)
FILE_TO_ANALYZE = 'vince-kaminski-at-enron-com-combined.txt' 
analyze_stylometry(FILE_TO_ANALYZE)