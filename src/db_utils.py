import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from threading import Lock

# Global lock for thread safety
_db_lock = Lock()

# Singleton pattern for shared embedding model
_embedding_model = None

def get_client():
    """Initialize a persistent ChromaDB client."""
    with _db_lock:
        # Reinitialize the client to avoid caching issues
        return chromadb.PersistentClient(path="./chroma_db")

def get_collection(collection_name="text_embeddings"):
    """Retrieve or create a ChromaDB collection."""
    client = get_client()
    try:
        return client.get_collection(collection_name)
    except Exception:
        return client.create_collection(name=collection_name)

def get_embedding_model():
    """Lazy initialization of embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

def insert_documents(documents, collection_name="text_embeddings"):
    """Insert or update documents with thread-safe access."""
    collection = get_collection(collection_name)
    model = get_embedding_model()

    # Generate embeddings
    embeddings = model.encode(documents).tolist()

    # Create unique IDs
    ids = [f"doc_{abs(hash(doc))}" for doc in documents]

    # Insert with lock
    with _db_lock:
        before_count = collection.count()
        collection.upsert(documents=documents, embeddings=embeddings, ids=ids)
        after_count = collection.count()

    print(f"✅ Inserted {after_count - before_count} documents.")


# def insert_documents(documents, collection_name="text_embeddings"):
#     """Insert or update documents and flush the database."""
#     collection = get_collection(collection_name)
#     model = get_embedding_model()

#     # Generate embeddings
#     embeddings = model.encode(documents).tolist()

#     # Create unique IDs based on content
#     ids = [f"doc_{hash(doc)}" for doc in documents]

#     # Upsert documents (insert or update)
#     collection.upsert(
#         embeddings=embeddings,
#         documents=documents,
#         ids=ids
#     )

#     # Manually force a database sync
#     client = get_client()
#     client.get_collection(collection_name).count()  # Forces a cache refresh

#     print(f"✅ Inserted/updated {len(documents)} documents.")

def query_documents(query, top_k=3, collection_name="text_embeddings"):
    """Query the database for the most recent documents."""
    # Open a fresh client to avoid cache issues
    client = get_client()
    collection = client.get_collection(collection_name)
    model = get_embedding_model()

    # Generate query embedding
    query_embedding = model.encode([query]).tolist()

    # Query ChromaDB
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    # Extract and return retrieved documents
    retrieved_docs = [doc for sublist in results['documents'] for doc in sublist]
    return retrieved_docs

def view_all_documents(collection_name="text_embeddings"):
    """Retrieve and display all documents from the specified ChromaDB collection."""
    # Initialize the client
    client = chromadb.PersistentClient(path="./chroma_db")

    # Get the specified collection
    collection = client.get_collection(collection_name)

    # Query all documents by passing an empty query string and requesting all results
    results = collection.query(query_texts=[""], n_results=1000)  # Adjust n_results if needed

    # Print the results
    for idx, doc in enumerate(results['documents']):
        print(f"Document {idx + 1}: {doc}")