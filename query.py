from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = Chroma(
    persist_directory="./dialogue_chroma_db",
    embedding_function=embeddings
)

# Now you can query it
def retrieve(query):
    results = vectorstore.similarity_search(query, k=3)

    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Content: {result.page_content[:200]}...")
        print(f"Metadata: {result.metadata}")
        print("-" * 50)

# Search with scores
    results_with_scores = vectorstore.similarity_search_with_score(query, k=3)
    for doc, score in results_with_scores:
        print(f"Score: {score:.4f}")
        print(f"Content: {doc.page_content[:100]}...")
        print("-" * 30)
    return results[0].page_content