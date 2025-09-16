import json
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
from transformers import Trainer, TrainingArguments
from sklearn.metrics import classification_report, accuracy_score
import random
import numpy as np

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# Load your JSON list of dialogues
with open('dataset/merged.json') as f:
    data = json.load(f)

# Label: 1 if speakers are same else 0
for entry in data:
    if "true" in entry["speaker_same"]:
        entry["label"] = 1
    else:
        entry["label"] = 0

# Shuffle and limit data
random.shuffle(data)


# Split 70% train, 15% validation, 15% test
train_idx = int(0.7 * len(data))
val_idx = int(0.85 * len(data))

train_data = data[:train_idx]
val_data = data[train_idx:val_idx]
test_data = data[val_idx:]

# Print dataset statistics
def print_dataset_stats(dataset, name):
    true_count = sum(1 for d in dataset if d["label"] == 1)
    false_count = sum(1 for d in dataset if d["label"] == 0)
    print(f"{name}: {len(dataset)} samples, {true_count} same speaker, {false_count} different speaker")
    print(f"{name} balance: {true_count/len(dataset):.2%} same speaker")

print_dataset_stats(train_data, "Train")
print_dataset_stats(val_data, "Validation")
print_dataset_stats(test_data, "Test")

# Initialize tokenizer and model
tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
model = RobertaForSequenceClassification.from_pretrained("roberta-base", num_labels=2)

def prepare_encodings(data_subset):
    texts = [(d["dialogues"][0], d["dialogues"][1]) for d in data_subset]
    labels = [d["label"] for d in data_subset]
    
    encodings = tokenizer(
        [x[0] for x in texts],
        [x[1] for x in texts],
        truncation=True,
        padding='max_length',
        max_length=512,
        return_tensors="pt"
    )
    return encodings, labels

train_encodings, train_labels = prepare_encodings(train_data)
val_encodings, val_labels = prepare_encodings(val_data)
test_encodings, test_labels = prepare_encodings(test_data)

class DialogueDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    
    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item
    
    def __len__(self):
        return len(self.labels)

# Create datasets
train_dataset = DialogueDataset(train_encodings, train_labels)
val_dataset = DialogueDataset(val_encodings, val_labels)
test_dataset = DialogueDataset(test_encodings, test_labels)

# Define compute_metrics function for evaluation
def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    accuracy = accuracy_score(labels, predictions)
    return {'accuracy': accuracy}

# Training arguments with validation
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=4,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    greater_is_better=True,
    logging_dir="./logs",
    logging_steps=50,
    warmup_steps=100,
    weight_decay=0.01,
    learning_rate=2e-5,
)

# Initialize trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,  # Use validation set for monitoring
    compute_metrics=compute_metrics,
)

# Train the model
print("Starting training...")
trainer.train()

# Save the trained model
print("Saving trained model...")
trainer.save_model("./finetuned_roberta")
tokenizer.save_pretrained("./finetuned_roberta")

# Evaluate on test set
print("Evaluating on test set...")
test_predictions = trainer.predict(test_dataset)
test_pred_labels = np.argmax(test_predictions.predictions, axis=1)

# Calculate and print metrics
test_accuracy = accuracy_score(test_labels, test_pred_labels)
print(f"\nTest Accuracy: {test_accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(test_labels, test_pred_labels, 
                          target_names=['Different Speaker', 'Same Speaker']))

# Optional: Print some example predictions
print("\nSample predictions:")
for i in range(min(5, len(test_data))):
    actual = test_labels[i]
    predicted = test_pred_labels[i]
    confidence = torch.softmax(torch.tensor(test_predictions.predictions[i]), dim=0).max().item()
    
    print(f"Example {i+1}:")
    print(f"  Dialogue 1: {test_data[i]['dialogues'][0][:100]}...")
    print(f"  Dialogue 2: {test_data[i]['dialogues'][1][:100]}...")
    print(f"  Actual: {'Same' if actual == 1 else 'Different'}")
    print(f"  Predicted: {'Same' if predicted == 1 else 'Different'}")
    print(f"  Confidence: {confidence:.3f}")
    print()