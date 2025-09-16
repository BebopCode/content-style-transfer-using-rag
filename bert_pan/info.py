import json

# Read the file line by line
with open('dataset/truncated_data.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Print the word counts of 'Text 1' and 'Text 2' for the first 10 entries
for i, entry in enumerate(data[:10], 1):
    text1, text2 = entry["pair"]
    words_text1 = len(text1.split())
    words_text2 = len(text2.split())
    
    print(f"\nEntry {i}:")
    print(f"  Words in Text 1: {words_text1}")
    print(f"  Words in Text 2: {words_text2}")
