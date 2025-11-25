import json
import random

# Load the full merged.json
with open('dataset/merged.json', 'r') as f:
    data = json.load(f)

# Separate into true and false
true_samples = [d for d in data if d["speaker_same"] == "true"]
false_samples = [d for d in data if d["speaker_same"] == "false"]

# Shuffle to randomize selection
random.shuffle(true_samples)
random.shuffle(false_samples)

# Take 50 of each
true_50 = true_samples[:50]
false_50 = false_samples[:50]

# Combine and shuffle
test_data = true_50 + false_50
random.shuffle(test_data)

# Save to new file
with open('dataset/test_100.json', 'w') as f:
    json.dump(test_data, f, indent=2)

print("✅ test_100.json created with 50 true and 50 false samples.")
