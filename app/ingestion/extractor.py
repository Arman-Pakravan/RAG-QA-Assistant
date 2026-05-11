"""PDF text extraction using pdfplumber."""
from pathlib import Path
from typing import List, Dict
import pdfplumber


def extract_pdf(file_path: str) -> List[Dict]:
    """
    Extract text from a PDF file, page by page.

    Returns a list of dicts:
      [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]
    """
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page": i, "text": text})
    return pages


def get_document_name(file_path: str) -> str:
    """Get a clean document name from the file path."""
    return Path(file_path).stem