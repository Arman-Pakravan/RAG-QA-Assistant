"""Text cleaning utilities."""
import re


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text:
      - Fix hyphenated line breaks (e.g. "compli-\nance" -> "compliance")
      - Collapse single newlines inside paragraphs into spaces
      - Preserve paragraph breaks (double newlines)
      - Strip page numbers and trailing whitespace
      - Collapse repeated whitespace
    """
    # Fix hyphenated line breaks: "word-\nword" -> "wordword"
    text = re.sub(r"-\n(\w)", r"\1", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Preserve paragraph breaks (2+ newlines) but join single newlines with space
    # First mark paragraph breaks with a placeholder
    text = re.sub(r"\n\s*\n", "<<PARA>>", text)
    # Join remaining single newlines with space
    text = re.sub(r"\n+", " ", text)
    # Restore paragraph breaks
    text = text.replace("<<PARA>>", "\n\n")

    # Remove standalone page numbers (e.g. "Page 12" or just "12" on its own line)
    text = re.sub(r"\n\s*(Page\s+)?\d+\s*\n", "\n", text)

    # Collapse repeated whitespace (but keep paragraph breaks)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


HEADING_PATTERNS = [
    re.compile(r"^\s*\d+(\.\d+)*\.?\s+[A-Z].{0,80}$"),    # "1. Introduction" / "2.3 Scope"
    re.compile(r"^\s*[A-Z][A-Z\s]{3,80}$"),               # ALL CAPS HEADING
    re.compile(r"^\s*(Chapter|Section|Part)\s+\d+.{0,80}$", re.I),
]


def looks_like_heading(line: str) -> bool:
    """Heuristic: does this line look like a heading?"""
    line = line.strip()
    if not line or len(line) > 100:
        return False
    return any(p.match(line) for p in HEADING_PATTERNS)