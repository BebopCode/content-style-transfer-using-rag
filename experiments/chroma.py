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
        """
        Initializes the EmailEmbeddingStore with automatic device detection.
        Prefers GPU (CUDA/ROCm) if available, falls back to CPU.
        """
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Detect available device
        if torch.cuda.is_available():
            self.device = "cuda"
            print(f"✓ Using GPU: {torch.cuda.get_device_name(0)}")
            print(f"  PyTorch version: {torch.__version__}")
            print(f"  CUDA/ROCm available: {torch.cuda.is_available()}")
            print(f"  Number of GPUs: {torch.cuda.device_count()}")
        else:
            self.device = "cpu"
            print("⚠ GPU not available, using CPU")
            print(f"  PyTorch version: {torch.__version__}")
        
        # Load model with detected device
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
        
        # Verify the model is on the correct device
        model_device = next(self.embedding_model.parameters()).device
        print(f"✓ Model loaded on device: {model_device}")
        
        self.collection = self.client.get_or_create_collection(
            name="email_embeddings"
        )
    
    def add_email(self, email_db_object: EmailDB):
            """
            Add a single email embedding to ChromaDB by extracting 
            message_id, content, and sender from the EmailDB object.
            """
            # --- Extraction: message_id, content, and sender are used ---
            message_id = str(email_db_object.id)
            content = email_db_object.content
            sender = email_db_object.sender  # <-- New: Extract sender
            # --------------------------------------------------------

            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Prepare metadata dictionary
            metadata = {
                "sender": sender
            }
            
            # Add to collection
            self.collection.add(
                ids=[message_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]  # <-- New: Include the metadata
            )
            print(f"added mail with mail ID {EmailDB.message_id} to Embedding store")
    
    def add_emails_batch(self, email_db_objects: list['EmailDB'], batch_size=100):
        """
        Add multiple emails in batches with progress tracking.
        Processes emails in smaller batches to provide progress updates and manage memory.
        
        Args:
            email_db_objects: List of EmailDB objects to add
            batch_size: Number of emails to process in each batch (default: 100)
        """
        total_emails = len(email_db_objects)
        print(f"Starting to add {total_emails} emails to ChromaDB in batches of {batch_size}...")
        
        # Process in batches
        for i in tqdm(range(0, total_emails, batch_size), desc="Adding email batches"):
            batch = email_db_objects[i:i + batch_size]
            
            ids = []
            contents = []
            metadatas = []
            
            for email_db_object in batch:
                ids.append(str(email_db_object.id))
                contents.append(email_db_object.content)
                metadatas.append({
                    "sender": email_db_object.sender
                })
            
            # Generate embeddings in batch
            print(f"  Encoding batch {i//batch_size + 1}/{(total_emails + batch_size - 1)//batch_size}...", end=" ")
            embeddings = self.embedding_model.encode(
                contents,
                show_progress_bar=False,
                batch_size=32  # SentenceTransformer internal batch size
            ).tolist()
            print("✓")
            
            # Add to collection
            print(f"  Adding to ChromaDB...", end=" ")
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            print("✓")
        
        print(f"✓ Successfully added all {total_emails} emails to ChromaDB")
    
    def search_similar_emails(self, query: str, n_results: int = 5, sender_filter: str = None) -> list[dict]:
            """
            Searches for emails semantically similar to the query string, 
            with an optional filter for the sender.

            Args:
                query (str): The search string.
                n_results (int): The number of top similar results to return.
                sender_filter (str, optional): The exact sender's email address to filter by. 
                                            Defaults to None (no filter).

            Returns:
                list[dict]: A list of dictionaries with message_id, content, distance, and sender.
            """
            # 1. Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # 2. Prepare the WHERE clause for filtering
            where_clause = {}
            if sender_filter:
                # ChromaDB filters require the metadata key (sender) and the value to match
                where_clause["sender"] = sender_filter
            
            # 3. Search the Chroma collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause, # <-- NEW: Apply the sender filter here
                include=['documents', 'distances', 'metadatas'] 
            )
            
            # 4. Format the results for easy use
            formatted_results = []
            
            # Chroma returns lists of results (one list per query embedding)
            if results['ids']:
                result_ids = results['ids'][0]
                result_documents = results['documents'][0]
                result_distances = results['distances'][0]
                result_metadatas = results['metadatas'][0]
                
                for i in range(len(result_ids)):
                    formatted_results.append({
                        'message_id': result_ids[i],
                        'content': result_documents[i],
                        'distance': result_distances[i],
                        'sender': result_metadatas[i]['sender']
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
