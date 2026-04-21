"""
Document Ingestion Pipeline — turns PDFs, DOCX, HTML, TXT into
searchable chunks stored in a vector database.

Pipeline: extract text -> chunk -> embed -> store in Chroma.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

import structlog
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

logger = structlog.get_logger()

# Embedding model — works with OpenAI key (cheap, fast, good quality)
# When you switch to Anthropic for agents, embeddings still use OpenAI
EMBEDDING_MODEL = "text-embedding-3-small"


def get_embeddings():
    """Get the embedding model. Uses OpenAI embeddings regardless of LLM provider."""
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.openai_api_key,
    )


def get_vector_store(workspace_id: str = "default") -> Chroma:
    """Get or create a Chroma vector store for a workspace."""
    persist_dir = os.path.join(settings.chroma_persist_dir, workspace_id)
    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        collection_name=f"workspace_{workspace_id}",
        embedding_function=get_embeddings(),
        persist_directory=persist_dir,
    )


def extract_text(file_path: str) -> str:
    """Extract text from PDF, DOCX, HTML, or TXT files."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt" or suffix == ".md":
        return path.read_text(encoding="utf-8")

    elif suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {i + 1}]\n{text}")
        return "\n\n".join(pages)

    elif suffix == ".docx":
        from docx import Document as DocxDocument
        doc = DocxDocument(file_path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    elif suffix in (".html", ".htm"):
        from bs4 import BeautifulSoup
        html = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def generate_doc_id(file_path: str) -> str:
    """Generate a unique ID for a document based on path + content hash."""
    content = Path(file_path).read_bytes()
    return hashlib.md5(content).hexdigest()[:12]


async def ingest_file(
    file_path: str,
    workspace_id: str = "default",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    source_name: Optional[str] = None,
) -> dict:
    """
    Full ingestion pipeline for a single file.
    Returns: {"chunks_created": N, "doc_id": "...", "source": "..."}
    """
    path = Path(file_path)
    source = source_name or path.name
    doc_id = generate_doc_id(file_path)

    logger.info("Ingesting document", source=source, doc_id=doc_id, workspace=workspace_id)

    # Extract
    text = extract_text(file_path)
    if not text.strip():
        raise ValueError(f"No text extracted from {file_path}")
    logger.info("Text extracted", chars=len(text))

    # Chunk
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    logger.info("Chunks created", count=len(chunks))

    # Build metadata for each chunk
    metadatas = [
        {
            "source": source,
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]

    # Generate unique IDs for deduplication
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    # Store in vector DB
    vector_store = get_vector_store(workspace_id)
    vector_store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
    logger.info("Stored in vector DB", workspace=workspace_id, chunks=len(chunks))

    return {
        "doc_id": doc_id,
        "source": source,
        "chunks_created": len(chunks),
        "total_chars": len(text),
        "workspace_id": workspace_id,
    }


async def ingest_text(
    text: str,
    source_name: str,
    workspace_id: str = "default",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict:
    """Ingest raw text directly (useful for pasting content, URLs, etc.)."""
    doc_id = hashlib.md5(text.encode()).hexdigest()[:12]

    logger.info("Ingesting raw text", source=source_name, doc_id=doc_id)

    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    metadatas = [
        {
            "source": source_name,
            "doc_id": doc_id,
            "workspace_id": workspace_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]

    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    vector_store = get_vector_store(workspace_id)
    vector_store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)

    return {
        "doc_id": doc_id,
        "source": source_name,
        "chunks_created": len(chunks),
        "total_chars": len(text),
        "workspace_id": workspace_id,
    }


def search_docs(
    query: str,
    workspace_id: str = "default",
    top_k: int = 5,
) -> list[dict]:
    """Search the vector DB and return relevant chunks with metadata."""
    vector_store = get_vector_store(workspace_id)
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)

    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "doc_id": doc.metadata.get("doc_id", ""),
            "chunk_index": doc.metadata.get("chunk_index", 0),
            "relevance_score": round(score, 3),
        }
        for doc, score in results
    ]


def list_documents(workspace_id: str = "default") -> list[dict]:
    """List all ingested documents for a workspace."""
    vector_store = get_vector_store(workspace_id)
    collection = vector_store._collection
    all_data = collection.get(include=["metadatas"])

    docs = {}
    for meta in all_data["metadatas"]:
        doc_id = meta.get("doc_id", "unknown")
        if doc_id not in docs:
            docs[doc_id] = {
                "doc_id": doc_id,
                "source": meta.get("source", "unknown"),
                "total_chunks": meta.get("total_chunks", 0),
            }

    return list(docs.values())


def delete_document(doc_id: str, workspace_id: str = "default") -> int:
    """Delete all chunks for a document. Returns number of chunks deleted."""
    vector_store = get_vector_store(workspace_id)
    collection = vector_store._collection
    all_data = collection.get(include=["metadatas"])

    ids_to_delete = []
    for i, meta in enumerate(all_data["metadatas"]):
        if meta.get("doc_id") == doc_id:
            ids_to_delete.append(all_data["ids"][i])

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    logger.info("Deleted document", doc_id=doc_id, chunks=len(ids_to_delete))
    return len(ids_to_delete)
