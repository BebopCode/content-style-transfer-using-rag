import json
from transformers import RobertaTokenizer  # Or use BigBirdTokenizer if needed

# Load tokenizer
tokenizer = RobertaTokenizer.from_pretrained("roberta-base")  # or "google/bigbird-roberta-base"

# Load your dataset
with open("dataset/merged.json") as f:  # Replace with your file name
    data = json.load(f)

too_long = 0

print("Index | Token Length | Exceeds Limit")
print("-" * 35)

for idx, entry in enumerate(data):
    text1, text2 = entry["dialogues"]
    encoded = tokenizer.encode_plus(
        text1,
        text2,
        truncation=False,  # We want the full length to inspect
        padding=False,
        return_tensors=None
    )
    length = len(encoded["input_ids"])
    if length > 512:
        too_long += 1
    print(f"{idx:5} | {length:12} | {'YES' if length > 512 else 'NO'}")

print(f"\n🔍 Total entries exceeding 512 tokens: {too_long}/{len(data)}")