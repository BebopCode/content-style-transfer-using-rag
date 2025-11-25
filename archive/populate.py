import json
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 1. Load dialogue JSON
with open("dialogue.json", "r") as f:
    dialogue_data = json.load(f)

# 2. Convert each dialogue entry to a LangChain Document with metadata
documents = [
    Document(
        page_content=item["dialogue"],
        metadata={
            "speaker": item["speaker"],
            "line_number": item["line_number"]
        }
    )
    for item in dialogue_data
]

# 3. Split documents (optional for long dialogues)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=80
)
chunks = text_splitter.split_documents(documents)

# 4. Load HuggingFace embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 5. Create and persist the vectorstore
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./dialogue_chroma_db"
)

print(f"✅ Vector DB created with {len(chunks)} chunks")