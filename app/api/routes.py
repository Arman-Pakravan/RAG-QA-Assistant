"""API routes for the RAG QA assistant."""
from pathlib import Path
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.ingestion.extractor import extract_pdf, get_document_name
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_document
from app.embeddings.store import get_store
from app.query.classifier import classify_query
from app.query.retriever import retrieve
from app.query.generator import (
    generate_answer,
    generate_comparison,
    DATA_REDIRECT_MESSAGE,
)


router = APIRouter()


# --- Schemas ---

class AskRequest(BaseModel):
    query: str
    top_k: int | None = None


class CompareRequest(BaseModel):
    query: str
    doc_a: str
    doc_b: str
    top_k_per_doc: int | None = 4


# --- Helpers ---

def _retrieve_from_doc(store, query: str, doc_name: str, k: int):
    """Retrieve chunks filtered to a single document."""
    candidates = store.search(query, top_k=50)
    filtered = [c for c in candidates if c["metadata"].get("document_name") == doc_name]
    return filtered[:k]


def _confidence_from_score(top_score: float) -> str:
    if top_score >= 0.55:
        return "high"
    if top_score >= 0.3:
        return "medium"
    return "low"


# --- Document upload + serving ---

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF -> extract -> clean -> chunk -> embed -> index."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    upload_path = Path(settings.upload_dir) / file.filename
    with upload_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    pages = extract_pdf(str(upload_path))
    if not pages:
        raise HTTPException(status_code=422, detail="No extractable text found in PDF.")

    raw_text = "\n\n".join(p["text"] for p in pages)
    cleaned = clean_text(raw_text)

    document_name = get_document_name(str(upload_path))
    chunks = chunk_document(
        cleaned,
        document_name=document_name,
        min_tokens=settings.chunk_min_tokens,
        max_tokens=settings.chunk_max_tokens,
    )

    store = get_store()
    added = store.add_chunks(chunks)

    return {
        "document_name": document_name,
        "pages": len(pages),
        "chunks_indexed": added,
        "total_chunks_in_index": store.stats()["total_chunks"],
    }


@router.get("/documents")
def list_documents():
    """List all uploaded PDF files available for viewing."""
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.exists():
        return {"documents": []}
    files = sorted(
        [f.name for f in upload_dir.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    )
    return {
        "documents": [
            {"filename": f, "stem": Path(f).stem}
            for f in files
        ]
    }


@router.get("/documents/{filename}")
def get_document(filename: str):
    """Serve a PDF file inline so the browser can render it."""
    safe_name = Path(filename).name  # prevent directory traversal
    file_path = Path(settings.upload_dir) / safe_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")
    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are served.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=safe_name,
        headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
    )


# --- Q&A ---

@router.post("/ask")
def ask(request: AskRequest):
    """
    Main QA endpoint.
    Pipeline: classify -> (redirect if data) -> retrieve -> generate.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty.")

    qtype = classify_query(query)

    # Data short-circuit: don't retrieve, don't call LLM
    if qtype == "data":
        return {
            "query": query,
            "query_type": qtype,
            "answer": DATA_REDIRECT_MESSAGE,
            "confidence": None,
            "top_score": None,
            "sources": [],
            "retrieved": [],
        }

    chunks = retrieve(query, top_k=request.top_k)

    if not chunks:
        return {
            "query": query,
            "query_type": qtype,
            "answer": "I don't know based on the provided documents. (No documents are indexed yet, or no relevant content was found.)",
            "confidence": "low",
            "top_score": 0.0,
            "sources": [],
            "retrieved": [],
        }

    try:
        answer = generate_answer(query, qtype, chunks)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    top_score = max((c["score"] for c in chunks), default=0.0)
    confidence = _confidence_from_score(top_score)

    sources = [
        {
            "document_name": c["metadata"].get("document_name"),
            "section_title": c["metadata"].get("section_title"),
            "content_type": c["metadata"].get("content_type"),
            "score": round(c["score"], 4),
        }
        for c in chunks
    ]

    return {
        "query": query,
        "query_type": qtype,
        "answer": answer,
        "confidence": confidence,
        "top_score": round(top_score, 4),
        "sources": sources,
        "retrieved": [
            {
                "metadata": c["metadata"],
                "score": round(c["score"], 4),
                "text_preview": c["text"][:200] + ("..." if len(c["text"]) > 200 else ""),
            }
            for c in chunks
        ],
    }


@router.post("/compare")
def compare(request: CompareRequest):
    """
    Compare how two documents address a topic.
    Pulls top-k chunks from EACH doc separately, then asks Claude to compare.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty.")
    if request.doc_a == request.doc_b:
        raise HTTPException(status_code=400, detail="Pick two different documents.")

    store = get_store()
    k = request.top_k_per_doc or 4

    chunks_a = _retrieve_from_doc(store, query, request.doc_a, k)
    chunks_b = _retrieve_from_doc(store, query, request.doc_b, k)

    if not chunks_a and not chunks_b:
        return {
            "query": query,
            "doc_a": request.doc_a,
            "doc_b": request.doc_b,
            "answer": "I don't have content from either document that's relevant to this question.",
            "sources": [],
            "chunks_a_count": 0,
            "chunks_b_count": 0,
        }

    try:
        answer = generate_comparison(query, request.doc_a, chunks_a, request.doc_b, chunks_b)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    sources = []
    for c in chunks_a + chunks_b:
        sources.append({
            "document_name": c["metadata"].get("document_name"),
            "section_title": c["metadata"].get("section_title"),
            "content_type": c["metadata"].get("content_type"),
            "score": round(c["score"], 4),
        })

    return {
        "query": query,
        "doc_a": request.doc_a,
        "doc_b": request.doc_b,
        "answer": answer,
        "sources": sources,
        "chunks_a_count": len(chunks_a),
        "chunks_b_count": len(chunks_b),
    }


# --- Test / utility endpoints ---

@router.get("/classify")
def classify(q: str = Query(..., description="Query to classify")):
    """See how a query would be classified (no retrieval, no answer)."""
    return {"query": q, "query_type": classify_query(q)}


@router.get("/search")
def search(
    q: str = Query(...),
    top_k: int = Query(5, ge=1, le=20),
    diverse: bool = Query(True),
):
    """Retrieve the top-k chunks for a query (no LLM)."""
    results = retrieve(q, top_k=top_k, diverse=diverse)
    return {
        "query": q,
        "result_count": len(results),
        "results": [
            {
                "score": round(r["score"], 4),
                "metadata": r["metadata"],
                "text_preview": r["text"][:300] + ("..." if len(r["text"]) > 300 else ""),
            }
            for r in results
        ],
    }


@router.get("/stats")
def stats():
    return get_store().stats()


@router.post("/reset")
def reset():
    get_store().reset()
    return {"status": "reset", "stats": get_store().stats()}