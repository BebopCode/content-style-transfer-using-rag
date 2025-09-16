import json
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
from transformers import Trainer, TrainingArguments
import random
# Load your JSON list of dialogues
with open('dataset/merged.json') as f:
    data = json.load(f)

# Label: 1 if speakers are same else 0
for entry in data:
    if "true" in entry["speaker_same"]:
        entry["label"] = 1
    else:
        entry["label"] = 0

# Sort by line_number to ensure consistent split

random.shuffle(data)
data = data[:5000]
# Split 80% train, 20% test based on line_number
split_idx = int(0.8 * len(data))
train_data = data[:split_idx]
test_data = data[split_idx:]

train_true = sum(1 for d in train_data if d["label"] == 1)
train_false = sum(1 for d in train_data if d["label"] == 0)

# Count true and false in test_data
test_true = sum(1 for d in test_data if d["label"] == 1)
test_false = sum(1 for d in test_data if d["label"] == 0)

print(f"Train data: {train_true} true, {train_false} false")
print(f"Test data: {test_true} true, {test_false} false")

print(f'Train len:{len(train_data)}, Test len: {len(test_data)}')

# Extract dialogues and labels

tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
model = RobertaForSequenceClassification.from_pretrained("roberta-base", num_labels=2)

train_texts = [(d["dialogues"][0], d["dialogues"][1]) for d in train_data]
test_texts = [(d["dialogues"][0], d["dialogues"][1]) for d in test_data]
train_labels = [d["label"] for d in train_data]
test_labels = [d["label"] for d in test_data]
train_encodings = tokenizer(
    [x[0] for x in train_texts],
    [x[1] for x in train_texts],
    truncation=True,
    padding='max_length',
    max_length=512,
    return_tensors="pt"
)

test_encodings = tokenizer(
    [x[0] for x in test_texts],
    [x[1] for x in test_texts],
    truncation=True,
    padding='max_length',
    max_length=512,
    return_tensors="pt"
)

class DialogueDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    
    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    
    def __len__(self):
        return len(self.labels)
    

train_dataset = DialogueDataset(train_encodings, train_labels)
test_dataset = DialogueDataset(test_encodings, test_labels)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    eval_strategy="epoch",
    save_strategy="no",
    logging_dir="./logs",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)
trainer.save_model("./finetuned_bert")
tokenizer.save_pretrained("./finetuned_bert")
trainer.train()

preds = trainer.predict(test_dataset)
pred_labels = torch.argmax(torch.tensor(preds.predictions), axis=1)
from sklearn.metrics import classification_report
print(classification_report(test_labels, pred_labels))