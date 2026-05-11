"""FAISS-backed vector store for document chunks."""
from pathlib import Path
from typing import List, Dict, Optional
import json
import threading

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.config import settings


class VectorStore:
    """
    A simple FAISS vector store with on-disk persistence.

    - Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384-dim, local, free)
    - Index: FAISS IndexFlatIP (inner product on L2-normalized vectors == cosine sim)
    - Metadata + texts stored alongside in a JSON file
    """

    def __init__(self, index_dir: str, model_name: str):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "faiss.index"
        self.meta_path = self.index_dir / "meta.json"

        self._lock = threading.Lock()
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

        self.index: Optional[faiss.Index] = None
        self.records: List[Dict] = []  # parallel to FAISS rows: {"text": ..., "metadata": {...}}

        self._load()

    # ---------- persistence ----------
    def _load(self):
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with self.meta_path.open("r", encoding="utf-8") as f:
                self.records = json.load(f)
        else:
            self.index = faiss.IndexFlatIP(self._dim)
            self.records = []

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        with self.meta_path.open("w", encoding="utf-8") as f:
            json.dump(self.records, f, ensure_ascii=False, indent=2)

    # ---------- embedding ----------
    def _embed(self, texts: List[str]) -> np.ndarray:
        """Encode texts and L2-normalize so inner product == cosine similarity."""
        vectors = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.astype("float32")

    # ---------- public API ----------
    def add_chunks(self, chunks: List[Dict]) -> int:
        """
        Add chunks to the index. Each chunk: {"text": str, "metadata": dict}.
        Returns the number of chunks added.
        """
        if not chunks:
            return 0

        with self._lock:
            texts = [c["text"] for c in chunks]
            vectors = self._embed(texts)
            self.index.add(vectors)
            self.records.extend(chunks)
            self._save()
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Return top_k most similar chunks for a query.
        Each result: {"score": float, "text": str, "metadata": {...}}
        """
        if self.index.ntotal == 0:
            return []

        with self._lock:
            q_vec = self._embed([query])
            scores, idxs = self.index.search(q_vec, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            rec = self.records[idx]
            results.append({
                "score": float(score),
                "text": rec["text"],
                "metadata": rec["metadata"],
            })
        return results

    def search_diverse(self, query: str, top_k: int = 5, fetch_k: int = 15) -> List[Dict]:
        """
        Retrieve with a diversity preference: pull more candidates, then
        cap how many come from the same section to avoid redundant context.
        """
        candidates = self.search(query, top_k=fetch_k)
        if len(candidates) <= top_k:
            return candidates

        seen_sections: Dict[str, int] = {}
        max_per_section = max(1, top_k // 2)  # at most ~half from one section
        diverse: List[Dict] = []

        for cand in candidates:
            section = cand["metadata"].get("section_title", "")
            if seen_sections.get(section, 0) >= max_per_section:
                continue
            diverse.append(cand)
            seen_sections[section] = seen_sections.get(section, 0) + 1
            if len(diverse) >= top_k:
                break

        # If diversity filtering left us short, top up with the next best candidates
        if len(diverse) < top_k:
            taken_ids = {id(d) for d in diverse}
            for cand in candidates:
                if id(cand) not in taken_ids:
                    diverse.append(cand)
                    if len(diverse) >= top_k:
                        break

        return diverse

    def stats(self) -> Dict:
        return {
            "total_chunks": int(self.index.ntotal) if self.index else 0,
            "documents": sorted({
                r["metadata"].get("document_name", "")
                for r in self.records
            }),
            "embedding_dim": self._dim,
        }

    def reset(self):
        """Wipe the index. Useful for testing."""
        with self._lock:
            self.index = faiss.IndexFlatIP(self._dim)
            self.records = []
            if self.index_path.exists():
                self.index_path.unlink()
            if self.meta_path.exists():
                self.meta_path.unlink()


# Singleton — initialized on first import
_store: Optional[VectorStore] = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(
            index_dir=settings.index_dir,
            model_name=settings.embedding_model,
        )
    return _store