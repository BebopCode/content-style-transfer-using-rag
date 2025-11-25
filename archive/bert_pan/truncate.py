import json

input_path = 'dataset/data.jsonl'
output_path = 'dataset/truncated_data.jsonl'

text_length = 150
def truncate(text):
    return ' '.join(text.split()[:text_length])

with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
    for line in infile:
        entry = json.loads(line)
        text1, text2 = entry["pair"]
        
        entry["pair"] = [
            truncate(text1),
            truncate(text2)
        ]
        
        outfile.write(json.dumps(entry) + '\n')

print("Truncated file saved as:", output_path)
