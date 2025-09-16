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
def retrieve(query, speaker=None):
    # Build filter if speaker is provided
    search_filter = {"speaker": speaker} if speaker else None

    # Search with filter
    results = vectorstore.similarity_search(query, k=3, filter=search_filter)


    # Search with scores (also with filter)
    results_with_scores = vectorstore.similarity_search_with_score(query, k=3, filter=search_filter)
    for doc, score in results_with_scores:
        print(f"Score: {score:.4f}")
        print(f"Speaker: {doc.metadata.get('speaker')}")
        print(f"Content: {doc.page_content}")
        print(f"len: {len(doc.page_content)}")
        print("-" * 30)

    return results[0].page_content if results else None