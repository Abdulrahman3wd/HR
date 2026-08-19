"""
ingestion.py
============
Reads a company's documents (txt / docx / pdf), splits them into chunks,
and stores them in that company's isolated vector collection.
"""

from pathlib import Path

from app.config import DOCS_BASE_FOLDER, CHROMA_DB_FOLDER, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
from app.vector_store import _collection_name
import chromadb
from chromadb.utils import embedding_functions


def get_company_docs_folder(company_id: int) -> Path:
    return DOCS_BASE_FOLDER / f"company_{company_id}"


def read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_document(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return read_txt(path)
    elif ext == ".docx":
        return read_docx(path)
    elif ext == ".pdf":
        return read_pdf(path)
    else:
        print(f"[SKIPPED] Unsupported file type: {path.name}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def rebuild_index(company_id: int) -> dict:
    """Rebuilds the vector index for ONE company from its own docs folder only."""
    docs_path = get_company_docs_folder(company_id)
    docs_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DB_FOLDER))
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collection_name = _collection_name(company_id)

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(name=collection_name, embedding_function=embedding_fn)

    total_chunks = 0
    processed_files = []

    for file_path in docs_path.iterdir():
        if not file_path.is_file():
            continue

        text = load_document(file_path)
        if not text.strip():
            continue

        chunks = chunk_text(text)
        ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file_path.name, "chunk_index": i} for i in range(len(chunks))]

        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        total_chunks += len(chunks)
        processed_files.append(file_path.name)

    return {"total_chunks": total_chunks, "processed_files": processed_files}