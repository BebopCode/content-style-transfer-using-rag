import json


truncated_path = 'dataset/truncated_data.jsonl'
truth_path = 'dataset/truth.jsonl'
output_path = 'dataset/merged.json'

truth_dict = {}
with open(truth_path, 'r') as truth_file:
    for line in truth_file:
        entry = json.loads(line)
        truth_dict[entry['id']] = str(entry['same']).lower()  # Convert to string: "true"/"false"

merged_data = []

with open(truncated_path, 'r') as truncated_file:
    for line in truncated_file:
        entry = json.loads(line)
        entry_id = entry['id']

        if entry_id in truth_dict:
            merged_entry = {
                "speaker_same": truth_dict[entry_id],
                "dialogues": entry["pair"]
            }
            merged_data.append(merged_entry)

with open(output_path, 'w') as output_file:
    json.dump(merged_data, output_file, indent=2)

print("Merged JSON file saved as:", output_path)