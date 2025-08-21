"""
Micro RAG (Retrieval Augmented Generation) for chi_llm.

Provides lightweight, zero‑configuration RAG using SQLite and local embeddings.

Supports two embedding backends:
1. FastEmbed (preferred): lightweight ONNX models
   (e.g., BAAI/bge-small-en-v1.5 ~34MB)
2. SentenceTransformers (fallback): PyTorch models
   (e.g., all-MiniLM-L6-v2, 90MB+)

Auto-detects FastEmbed when available; otherwise falls back
to sentence-transformers gracefully.
"""

import sqlite3
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from .core import MicroLLM

# Optional imports with graceful fallback
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Try FastEmbed first (preferred - lightweight)
try:
    from fastembed import TextEmbedding

    HAS_FASTEMBED = True
except ImportError:
    HAS_FASTEMBED = False

# Fallback to sentence-transformers
try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

# Check if any embedding backend is available
HAS_EMBEDDINGS = HAS_FASTEMBED or HAS_SENTENCE_TRANSFORMERS

try:
    import sqlite_vec

    HAS_SQLITE_VEC = True
except ImportError:
    HAS_SQLITE_VEC = False


@dataclass
class Document:
    """Represents a document in the RAG system."""

    id: str
    content: str
    metadata: Dict[str, Any] = None
    embedding: Optional[np.ndarray] = None


class MicroRAG:
    """
    Zero-configuration RAG system using local models and SQLite.

    Features:
    - Auto-detects embedding backend (FastEmbed preferred,
      sentence-transformers fallback)
    - FastEmbed: lightweight 34MB ONNX models for edge deployments
    - SentenceTransformers: PyTorch models for full compatibility
    - SQLite vector storage with sqlite-vec for efficient similarity search
    - Zero configuration: works out of the box with sensible defaults

    Example:
        >>> from chi_llm.rag import MicroRAG
        >>> rag = MicroRAG()  # Uses intfloat/multilingual-e5-base by default
        >>>
        >>> # Add documents (works with 100+ languages)
        >>> rag.add_document("Python to język programowania")
        >>> rag.add_document("Stworzył go Guido van Rossum")
        >>>
        >>> # Query in any language
        >>> response = rag.query("Kto stworzył Pythona?")
        >>> print(response)
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        llm: Optional[MicroLLM] = None,
        config_path: Optional[str] = None,
        auto_init: bool = True,
    ):
        """
        Initialize MicroRAG with optional configuration.

        Args:
            db_path: Path to SQLite database (default: ~/.cache/chi_llm/rag.db)
            embedding_model: Model for embeddings. Defaults:
                - FastEmbed: intfloat/multilingual-e5-base
                  (280MB, 768 dims, 100+ languages)
                - SentenceTransformers: all-MiniLM-L6-v2
                  (90MB, 384 dims, English)
            llm: MicroLLM instance (creates new if not provided)
            config_path: Path to YAML configuration file
            auto_init: Automatically initialize database and models
        """
        self._check_dependencies()

        # Load config if provided
        self.config = self._load_config(config_path) if config_path else {}

        # Set up paths
        self.db_path = db_path or self.config.get(
            "db_path", str(Path.home() / ".cache" / "chi_llm" / "rag.db")
        )

        # Initialize components
        self.llm = llm or MicroLLM()

        # Auto-detect embedding backend and set default model
        self.embedding_backend = self._detect_embedding_backend()
        self.embedding_model_name = embedding_model or self.config.get(
            "embedding_model", self._get_default_embedding_model()
        )

        self.embedding_model = None
        self.conn = None

        if auto_init:
            self.initialize()

    def _check_dependencies(self):
        """Check if required dependencies are installed."""
        missing = []
        if not HAS_NUMPY:
            missing.append("numpy")
        if not HAS_EMBEDDINGS:
            missing.append("fastembed or sentence-transformers")
        if not HAS_SQLITE_VEC:
            missing.append("sqlite-vec")

        if missing:
            installation_options = [
                "pip install chi-llm[rag]  # Full RAG",
                "pip install chi-llm[rag-lite]  # FastEmbed only",
                f"pip install {' '.join(missing)}  # Individual packages",
            ]
            raise ImportError(
                "RAG features require additional dependencies. Install with:\n"
                + "\n".join(installation_options)
            )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _detect_embedding_backend(self) -> str:
        """Detect available embedding backend, preferring FastEmbed."""
        if HAS_FASTEMBED:
            return "fastembed"
        elif HAS_SENTENCE_TRANSFORMERS:
            return "sentence-transformers"
        else:
            raise ImportError(
                "No embedding backend available. Install fastembed or "
                "sentence-transformers."
            )

    def _get_default_embedding_model(self) -> str:
        """Get default embedding model based on available backend."""
        if self.embedding_backend == "fastembed":
            return "intfloat/multilingual-e5-base"  # 280MB, 768 dims, 100+ languages
        else:
            return "sentence-transformers/all-MiniLM-L6-v2"  # 90MB, PyTorch

    def _load_embedding_model(self):
        """Load embedding model using the detected backend."""
        if self.embedding_backend == "fastembed":
            return FastEmbedWrapper(self.embedding_model_name)
        else:
            return SentenceTransformerWrapper(self.embedding_model_name)

    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension for the current model."""
        if self.embedding_backend == "fastembed":
            # Common FastEmbed model dimensions
            if "bge-small" in self.embedding_model_name.lower():
                return 384
            elif "bge-base" in self.embedding_model_name.lower():
                return 768
            elif "bge-large" in self.embedding_model_name.lower():
                return 1024
            else:
                return 384  # Default for most small models
        else:
            # Common sentence-transformers dimensions
            if "all-MiniLM-L6-v2" in self.embedding_model_name:
                return 384
            elif "all-mpnet-base-v2" in self.embedding_model_name:
                return 768
            else:
                return 384  # Safe default

    def initialize(self):
        """Initialize database and models."""
        # Create database directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite with vector extension
        self.conn = sqlite3.connect(self.db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)

        # Create tables
        self._create_tables()

        # Load embedding model
        print(
            "Loading embedding model: "
            f"{self.embedding_model_name} (using {self.embedding_backend})"
        )
        self.embedding_model = self._load_embedding_model()
        print("✅ RAG system ready!")

    def _create_tables(self):
        """Create necessary database tables."""
        cursor = self.conn.cursor()

        # Documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Embeddings table with vector column
        embedding_dim = self._get_embedding_dimension()
        cursor.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
                id TEXT PRIMARY KEY,
                embedding FLOAT[{embedding_dim}]
            )
        """
        )

        self.conn.commit()

    def add_document(
        self,
        content: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a document to the RAG system.

        Args:
            content: Document text
            doc_id: Optional document ID (auto-generated if not provided)
            metadata: Optional metadata dictionary

        Returns:
            Document ID
        """
        import uuid

        # Generate ID if not provided
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        # Generate embedding
        embedding = self.embedding_model.encode(content)

        # Store in database
        cursor = self.conn.cursor()

        # Insert document
        cursor.execute(
            "INSERT OR REPLACE INTO documents (id, content, metadata) VALUES (?, ?, ?)",
            (doc_id, content, json.dumps(metadata) if metadata else None),
        )

        # Insert embedding
        cursor.execute(
            "INSERT OR REPLACE INTO embeddings (id, embedding) VALUES (?, ?)",
            (doc_id, embedding.tolist()),
        )

        self.conn.commit()
        return doc_id

    def add_documents(self, documents: List[Union[str, Document]]) -> List[str]:
        """
        Add multiple documents at once.

        Args:
            documents: List of document strings or Document objects

        Returns:
            List of document IDs
        """
        doc_ids = []
        for doc in documents:
            if isinstance(doc, str):
                doc_id = self.add_document(doc)
            else:
                doc_id = self.add_document(doc.content, doc.id, doc.metadata)
            doc_ids.append(doc_id)
        return doc_ids

    def search(
        self, query: str, top_k: int = 3, threshold: float = 0.5
    ) -> List[Document]:
        """
        Search for relevant documents using vector similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of relevant documents
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        # Search using vector similarity
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                d.id,
                d.content,
                d.metadata,
                vec_distance_cosine(e.embedding, ?) as distance
            FROM embeddings e
            JOIN documents d ON e.id = d.id
            WHERE distance <= ?
            ORDER BY distance
            LIMIT ?
        """,
            (query_embedding.tolist(), 1 - threshold, top_k),
        )

        results = []
        for row in cursor.fetchall():
            doc = Document(
                id=row[0],
                content=row[1],
                metadata=json.loads(row[2]) if row[2] else None,
            )
            results.append(doc)

        return results

    def query(
        self,
        question: str,
        top_k: int = 3,
        threshold: float = 0.5,
        include_sources: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """
        Query the RAG system with a question.

        Args:
            question: Question to answer
            top_k: Number of context documents to retrieve
            threshold: Minimum relevance threshold
            include_sources: Whether to include source documents in response

        Returns:
            Answer string, or dict with answer and sources if include_sources=True
        """
        # Search for relevant documents
        relevant_docs = self.search(question, top_k, threshold)

        if not relevant_docs:
            # No relevant context, use LLM directly
            answer = self.llm.ask(question)
        else:
            # Build context from relevant documents
            context = "\n\n".join(
                [
                    f"Document {i+1}:\n{doc.content}"
                    for i, doc in enumerate(relevant_docs)
                ]
            )

            # Generate answer with context
            prompt = (
                "Based on the following context, answer the question.\n\n"
                "Context:\n"
                f"{context}\n\n"
                f"Question: {question}\n\n"
                "Answer based on the context provided. If the context "
                "doesn't contain the answer, say so."
            )

            answer = self.llm.generate(prompt)

        if include_sources:
            return {
                "answer": answer,
                "sources": [
                    {"id": doc.id, "content": doc.content[:200] + "..."}
                    for doc in relevant_docs
                ],
            }

        return answer

    def clear(self):
        """Clear all documents from the database."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM embeddings")
        self.conn.commit()

    def count_documents(self) -> int:
        """Get the number of documents in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        return cursor.fetchone()[0]

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    @classmethod
    def from_config(cls, config_path: str) -> "MicroRAG":
        """
        Create MicroRAG instance from YAML configuration file.

        Example config.yaml:
            db_path: ./my_knowledge.db
            embedding_model: BAAI/bge-small-en-v1.5  # FastEmbed (34MB)
            # embedding_model: sentence-transformers/all-MiniLM-L6-v2  # Alternative
            llm:
                temperature: 0.7
                max_tokens: 4096
            documents:
                - content: "Python is great"
                  metadata: {"type": "fact"}
                - content: "Machine learning is powerful"
                  metadata: {"type": "ml"}
        """
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Create LLM with config if provided
        llm_config = config.get("llm", {})
        llm = MicroLLM(**llm_config) if llm_config else None

        # Create RAG instance
        rag = cls(
            db_path=config.get("db_path"),
            embedding_model=config.get("embedding_model"),
            llm=llm,
            config_path=config_path,
        )

        # Load initial documents if provided
        if "documents" in config:
            for doc_config in config["documents"]:
                rag.add_document(
                    content=doc_config["content"],
                    doc_id=doc_config.get("id"),
                    metadata=doc_config.get("metadata"),
                )

        return rag


class FastEmbedWrapper:
    """Wrapper for FastEmbed to provide unified interface."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = TextEmbedding(model_name=model_name)

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings."""
        if isinstance(texts, str):
            texts = [texts]

        # FastEmbed returns generator, convert to list then numpy array
        embeddings = list(self.model.embed(texts))
        return np.array(embeddings[0] if len(embeddings) == 1 else embeddings)


class SentenceTransformerWrapper:
    """Wrapper for SentenceTransformers to provide unified interface."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings."""
        return self.model.encode(texts)


# Convenience function for quick RAG
def quick_rag(question: str, documents: List[str]) -> str:
    """
    Quick RAG query without persistence.

    Example:
        >>> from chi_llm.rag import quick_rag
        >>> docs = [
        ...     "Python was created by Guido van Rossum",
        ...     "Python is a high-level programming language"
        ... ]
        >>> answer = quick_rag("Who created Python?", docs)
    """
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        with MicroRAG(db_path=tmp.name) as rag:
            rag.add_documents(documents)
            return rag.query(question)
