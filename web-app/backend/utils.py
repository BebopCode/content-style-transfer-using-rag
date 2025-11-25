import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings

def embedding_to_blob(vec):
    return np.array(vec, dtype=np.float32).tobytes()

def blob_to_embedding(blob):
    return np.frombuffer(blob, dtype=np.float32)

emb = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)