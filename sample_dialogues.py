import json
import random

# Load original JSON
with open("dialogue.json", "r") as f:
    dialogues = json.load(f)

max_index = len(dialogues) - 1
if max_index < 1:
    raise ValueError("Not enough dialogues to sample from.")

result = []
true_count = 0
false_count = 0
false_limit = 6482

# Keep sampling until we get 10,000 valid pairs
while len(result) < 10000:
    i, j = random.sample(range(max_index + 1), 2)
    d1 = dialogues[i]
    d2 = dialogues[j]

    same_speaker = d1["speaker"] == d2["speaker"]

    # Enforce false_count limit
    if not same_speaker and false_count >= false_limit:
        continue  # skip and sample again

    result.append({
        "speaker_same": "true" if same_speaker else "false",
        "dialogues": [d1["dialogue"].strip(), d2["dialogue"].strip()]
    })

    if same_speaker:
        true_count += 1
    else:
        false_count += 1

# 🔀 Shuffle the final dataset
random.shuffle(result)

# Save to file
with open("sampled_10000_random_pairs.json", "w") as f:
    json.dump(result, f, indent=2)

# Print summary
print(f"Total entries with speaker_same = true : {true_count}")
print(f"Total entries with speaker_same = false: {false_count}")
