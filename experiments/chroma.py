# chroma_client.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime
from .models import EmailDB
from tqdm import tqdm
import torch

class EmailEmbeddingStore:
    def __init__(self, persist_directory="./experiments/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Device detection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load an asymmetric model (E5 is a top performer for this)
        # We use 'small' to keep it fast, but 'base' or 'large' are available
        self.model_name = 'intfloat/e5-small-v2'
        self.embedding_model = SentenceTransformer(self.model_name, device=self.device)
        
        print(f"✓ Model {self.model_name} loaded on: {self.device}")
        
        self.collection = self.client.get_or_create_collection(
            name="email_embeddings_asymmetric"
        )

    def add_emails_batch(self, email_db_objects: list, batch_size=100):
        total_emails = len(email_db_objects)
        
        for i in tqdm(range(0, total_emails, batch_size), desc="Indexing Emails"):
            batch = email_db_objects[i:i + batch_size]
            
            ids = [str(e.id) for e in batch]
            # ASYMMETRIC STEP: Add "passage: " prefix to documents
            contents_to_embed = [f"passage: {e.content}" for e in batch]
            raw_contents = [e.content for e in batch] # Keep original for Chroma storage
            
            metadatas = [{"sender": e.sender} for e in batch]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                contents_to_embed,
                show_progress_bar=False,
                batch_size=32
            ).tolist()
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=raw_contents, 
                metadatas=metadatas
            )

    def search_similar_emails(self, query: str, n_results: int = 5, sender_filter: str = None) -> list[dict]:
        # ASYMMETRIC STEP: Add "query: " prefix to the user's search string
        query_with_prefix = f"query: {query}"
        query_embedding = self.embedding_model.encode(query_with_prefix).tolist()
        
        where_clause = {"sender": sender_filter} if sender_filter else {}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=['documents', 'distances', 'metadatas'] 
        )
        
        formatted_results = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'message_id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'distance': results['distances'][0][i],
                    'sender': results['metadatas'][0][i]['sender']
                })
                    
        return formatted_results
    
    def update_email(self, message_id: str, content: str):
        """Update an existing email embedding"""
        embedding = self.embedding_model.encode(content).tolist()
        
        self.collection.update(
            ids=[str(message_id)],
            embeddings=[embedding],
            documents=[content]
        )
    
    def delete_email(self, message_id: str):
        """Delete an email embedding"""
        self.collection.delete(ids=[str(message_id)])
    
    def get_email_by_message_id(self, message_id: str):
        """Retrieve a specific email by message_id"""
        result = self.collection.get(
            ids=[str(message_id)],
            include=["embeddings", "documents"]
        )
        return result
    
    def get_unique_senders(self) -> list[str]:
        """
        Retrieves all documents from the collection and extracts a list 
        of unique 'sender' values from the metadata.
        
        This is useful for debugging metadata filters and building UI lists.
        """
        # Fetch all items from the collection, requesting only metadatas.
        # Note: A large collection may require pagination (using limit/offset), 
        # but for typical use, fetching all is faster/simpler.
        try:
            results = self.collection.get(
                include=['metadatas']
            )
        except Exception as e:
            print(f"Error fetching data from ChromaDB: {e}")
            return []

        unique_senders = set()
        
        if results.get('metadatas'):
            for metadata in results['metadatas']:
                # Ensure the 'metadata' dictionary is not None and contains the 'sender' key
                if metadata and 'sender' in metadata:
                    unique_senders.add(metadata['sender'])
        
        # Convert the set (for uniqueness) back to a list
        return sorted(list(unique_senders))
    
if __name__ == "__main__":
    # 1. Initialize your store
    store = EmailEmbeddingStore()

    # 2. Define the test parameters
    test_query = "legal document"
    target_sender = "kay.mann@enron.co"

    print(f"--- Searching emails from {target_sender} ---")
    
    # 3. Call your function
    results = store.search_similar_emails(
        query=test_query, 
        n_results=50, 
        sender_filter=target_sender
    )

    # 4. Print the results
    if not results:
        print("No matches found.")
    for res in results:
        print(f"\nDistance: {res['distance']:.4f}")
        print(f"Content: {res['content']}...") # Print first 200 chars
        print("-" * 30)
