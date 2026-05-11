"""Retrieval wrapper around the vector store."""
from typing import List, Dict

from app.embeddings.store import get_store
from app.config import settings


def retrieve(query: str, top_k: int = None, diverse: bool = True) -> List[Dict]:
    """Retrieve top-k chunks for a query."""
    k = top_k or settings.top_k
    store = get_store()
    if diverse:
        return store.search_diverse(query, top_k=k)
    return store.search(query, top_k=k)