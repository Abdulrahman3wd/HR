"""
vector_store.py
===============
All interactions with ChromaDB.

Multi-tenant design: each company gets its own collection, named
"company_{company_id}_policies", so documents/embeddings from one company
are never visible to another company's queries.
"""

import chromadb
from chromadb.utils import embedding_functions
from app.config import CHROMA_DB_FOLDER, EMBEDDING_MODEL, TOP_K


def _collection_name(company_id: int) -> str:
    return f"company_{company_id}_policies"


def get_collection(company_id: int, create_if_missing: bool = False):
    client = chromadb.PersistentClient(path=str(CHROMA_DB_FOLDER))
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    name = _collection_name(company_id)

    if create_if_missing:
        return client.get_or_create_collection(name=name, embedding_function=embedding_fn)

    try:
        return client.get_collection(name=name, embedding_function=embedding_fn)
    except Exception:
        return None


def get_relevant_context(company_id: int, question: str, top_k: int = TOP_K):
    collection = get_collection(company_id)
    if collection is None:
        return [], []

    results = collection.query(query_texts=[question], n_results=top_k)
    docs = results["documents"][0]
    sources = [meta["source"] for meta in results["metadatas"][0]]
    return docs, sources