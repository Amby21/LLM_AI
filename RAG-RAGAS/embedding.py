import chromadb
from chromadb.utils import embedding_functions
from chunker import chunk_all_documents
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path = "./chroma_store")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-v6-v2")
collection = client.get_or_create_collection(name = "policy_docs", embedding_function=embedding_fn)


def setup(chunks: list):
    """Store chunks in ChromaDB. ChromaDB automatically embeds each chunk."""
    if collection.count() > 0:
        print(f"✅ ChromaDB already has "
              f"{collection.count()} chunks — skipping")
        return
    documents = [c["text"] for c in chunks]
    ids = [c['id'] for c in chunks]
    metadatas = [{"doc_title" : c["doc_title"], "doc_id": c["doc_id"]} for c in chunks]
    collection.add(documents=documents,metadatas=metadatas, ids=ids)
    print(f"Stored {collection.count()} Collection in Chromadb")

def search(query: str, n_results = 3, threshold = 0.5)-> list:
    """Search ChromaDB for relevant chunks."""
    results = collection.query(query_texts=[query],n_results=n_results)

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]
    distances = results["distances"][0]
    filtered =[]

    for doc, metadata, distance in zip(docs,metadatas,distances):
        similarity = 1 - distance
        if similarity >= threshold:
            filtered.append({"text":doc,
                "doc_title":  metadata["doc_title"],
                "similarity": round(similarity, 3)})
    
    return filtered

