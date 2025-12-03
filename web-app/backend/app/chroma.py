# chroma_client.py
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime
from .models import EmailDB

class EmailEmbeddingStore:
    def __init__(self, persist_directory="./chroma_db"):
        """
        Initializes the EmailEmbeddingStore.
        """
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self.client.get_or_create_collection(
            name="email_embeddings"
        )
    
    def add_email(self, email_db_object: EmailDB):
            """
            Add a single email embedding to ChromaDB by extracting 
            message_id, content, and sender from the EmailDB object.
            """
            # --- Extraction: message_id, content, and sender are used ---
            message_id = str(email_db_object.message_id)
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
    
    def add_emails_batch(self, email_db_objects: list['EmailDB']):
            """
            Add multiple emails at once (more efficient) by extracting 
            message_id, content, and sender from the list of EmailDB objects.
            """
            ids = []
            contents = []
            metadatas = [] # <-- New list for metadatas
            
            for email_db_object in email_db_objects:
                ids.append(str(email_db_object.message_id))
                contents.append(email_db_object.content)
                # Collect metadata for each email
                metadatas.append({
                    "sender": email_db_object.sender
                })
            
            # Generate embeddings in batch
            embeddings = self.embedding_model.encode(contents).tolist()
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas # <-- Pass the metadata list
            )
    
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


# Usage example with your SQLite database
if __name__ == "__main__":

    
    # Initialize embedding store
    embedding_store = EmailEmbeddingStore()
    print(embedding_store.get_unique_senders())
    # Get database session
    string="""
    When is the next meeting
    """
    dictionary = embedding_store.search_similar_emails(query=string,n_results=5, sender_filter='bhandariaaryan16@gmail.com')
    print(dictionary)