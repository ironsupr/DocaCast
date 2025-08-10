from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import faiss  # type: ignore


class VectorStore:
    """A simple in-memory vector store backed by FAISS IndexFlatL2.

    Keeps parallel arrays of texts and metadatas so FAISS indices map back to content.
    """

    def __init__(self, dim: Optional[int] = None):
        self.index: Optional[faiss.Index] = None
        self.dim: Optional[int] = None
        if dim is not None:
            # Use inner product (with normalized embeddings this is cosine similarity)
            self.index = faiss.IndexFlatIP(dim)
            self.dim = dim
        self.texts: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)
            self.dim = dim
        elif self.dim is not None and self.dim != dim:
            raise ValueError(f"Embedding dimension mismatch: store={self.dim}, incoming={dim}")

    def add_documents(self, processed_docs: List[Dict[str, Any]], filename: Optional[str] = None) -> int:
        """Add processed docs from process_pdf.

        Each item should have keys: text_chunk (str), embedding (List[float]), page_number (int).
        Optionally, a filename can be provided and attached to metadata.

        Returns the number of vectors added.
        """
        if not processed_docs:
            return 0

        embeddings = np.array([d["embedding"] for d in processed_docs], dtype=np.float32)
        self._ensure_index(embeddings.shape[1])

        self.index.add(embeddings)

        for d in processed_docs:
            text = d.get("text_chunk", "")
            page_number = int(d.get("page_number", 0))
            meta = {
                "page_number": page_number,
            }
            if filename:
                meta["filename"] = filename
            self.texts.append(text)
            self.metadatas.append(meta)

        return embeddings.shape[0]

    def search(self, query_embedding: List[float] | np.ndarray, k: int = 5, fetch_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for the top-k most similar chunks given a query embedding.

        Uses inner product on normalized vectors (i.e., cosine similarity).
        Returns a list of dicts with: text, metadata, score, distance (1 - score)
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        q = np.array(query_embedding, dtype=np.float32)
        if q.ndim == 1:
            q = q[None, :]
        if self.dim is not None and q.shape[1] != self.dim:
            raise ValueError(f"Query embedding dimension mismatch: store={self.dim}, query={q.shape[1]}")

        nprobe = fetch_k if fetch_k is not None else k
        distances, indices = self.index.search(q, nprobe)
        idxs = indices[0].tolist()
        dists = distances[0].tolist()

        results: List[Dict[str, Any]] = []
        for i, dist in zip(idxs, dists):
            if i < 0:
                continue
            score = float(dist)  # inner product on normalized vectors ∈ [-1, 1]
            results.append({
                "text": self.texts[i],
                "metadata": self.metadatas[i],
                "score": score,
                # Back-compat: pseudo-distance as (1 - score) for cosine
                "distance": 1.0 - score,
            })
        # Trim to k in case fetch_k > k
        return results[:k]
