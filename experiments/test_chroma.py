from .chroma import EmailEmbeddingStore


def main():
    # 1. Initialize the embedding store
    # Adjust arguments if your constructor differs
    store = EmailEmbeddingStore( )


    # 3. Test WITH sender filter
    print("\n=== Search with sender filter ===")
    results_filtered = store.search_similar_emails(
        query="project deadline update",
        n_results=5,
        sender_filter="kay.mann@enron.com"  # must match metadata exactly
    )

    for r in results_filtered:
        print("-" * 40)
        print("Message ID:", r["message_id"])
        print("Sender:", r["sender"])
        print("Distance:", r["distance"])
        print("Content:", r["content"][:200], "...")


if __name__ == "__main__":
    main()
