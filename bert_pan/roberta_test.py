import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import ollama
from query import retrieve
import torch.nn.functional as F

# Load saved model and tokenizer
model_path = "./finetuned_roberta"  # Path where you saved the model
tokenizer = RobertaTokenizer.from_pretrained(model_path)
model = RobertaForSequenceClassification.from_pretrained(model_path)
model.eval() 

def predict_dialogue(dialogue1, dialogue2):
    inputs = tokenizer(dialogue1, dialogue2, return_tensors="pt", truncation=True, padding=True)

    # Forward pass (no gradient calculation)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
    probs = F.softmax(logits, dim=1)
    # Get predicted class (0 or 1)
    predicted_class = torch.argmax(logits, dim=1).item()

    if predicted_class == 1:
        print(" Same Author")
    else:
        print("Not the Same")

    return probs



def chat(question, model='gemma:7b', speaker = ""):
    try:
        context = retrieve(question, speaker)
        response = ollama.chat(
            model=model,
            messages=[{
                'role': 'user',
                'content': f'You have to reply to this {question} in a certain writing style of this example - {context}'
            }],
            stream=False,
            options={"num_predict": 200}
        )
        reply = response['message']['content']
        print('LLM reply with context', reply)
        return reply, context
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None  

if __name__ == "__main__":
    print("Chat example")
    reply, context = chat(model="gemma:7b", question="What are your thoughts on theory of relativity?", speaker="GOLLUM")
    print('Context from RAG', context)

    # Check that both reply and context are non-empty strings
    if isinstance(reply, str) and isinstance(context, str) and reply.strip() and context.strip():
        confidence = predict_dialogue(reply, context)
        print(confidence)
    else:
        print(" Either reply or context is missing or invalid. Skipping prediction.")

# Example usage

