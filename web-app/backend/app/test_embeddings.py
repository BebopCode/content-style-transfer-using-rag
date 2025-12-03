from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize model (downloads on first run)
print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully!")

# Test with sample email content
email_content = "Meeting scheduled for next Tuesday at 2 PM to discuss project updates."

# Generate embedding
print("\nGenerating embedding...")
embedding = model.encode(email_content)

print(f"Embedding shape: {embedding.shape}")  # Should be (384,)
print(f"Embedding type: {type(embedding)}")
print(f"First 5 values: {embedding[:5]}")

# Test similarity between two texts
text1 = "Meeting about project timeline"
text2 = "Discussion on project schedule"
text3 = "Lunch menu for Friday"

embeddings = model.encode([text1, text2, text3])

# Calculate cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])

print(f"\nSimilarity between text1 and text2 (related): {sim_1_2:.4f}")
print(f"Similarity between text1 and text3 (unrelated): {sim_1_3:.4f}")

print("\n✓ Sentence Transformers is working correctly!")