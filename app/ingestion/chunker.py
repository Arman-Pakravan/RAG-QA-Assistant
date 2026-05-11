"""Smart text chunking with metadata."""
import re
from typing import List, Dict
import tiktoken

from app.ingestion.cleaner import looks_like_heading


# Use cl100k_base — it's the tokenizer for gpt-4o, gpt-4, gpt-3.5
_ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def split_into_sections(text: str) -> List[Dict]:
    """
    Split text into sections based on headings.
    Returns: [{"title": "...", "body": "..."}]
    If no headings detected, returns one section with title "Document".
    """
    lines = text.split("\n")
    sections = []
    current_title = "Introduction"
    current_lines: List[str] = []

    for line in lines:
        if looks_like_heading(line):
            # Save previous section
            if current_lines:
                sections.append({
                    "title": current_title,
                    "body": "\n".join(current_lines).strip(),
                })
            current_title = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        sections.append({
            "title": current_title,
            "body": "\n".join(current_lines).strip(),
        })

    # If no real sections were found, return the whole thing as one
    if not sections:
        sections = [{"title": "Document", "body": text}]

    return [s for s in sections if s["body"]]


def detect_content_type(text: str) -> str:
    """
    Classify a chunk's content type using simple heuristics.
    Returns one of: how_to | policy | explanation | reference
    """
    lower = text.lower()

    # how_to: numbered/bulleted steps or step-y verbs
    step_markers = len(re.findall(r"(?:^|\n)\s*(?:\d+\.|\d+\)|step\s+\d+|[-*•])\s", lower))
    if step_markers >= 3 or re.search(r"\bstep\s+\d+\b", lower):
        return "how_to"

    # policy: compliance/policy language
    policy_terms = ["must", "shall", "required", "prohibited", "policy",
                    "compliance", "mandatory", "is not permitted", "may not"]
    if sum(term in lower for term in policy_terms) >= 2:
        return "policy"

    # reference: tables, definitions, lots of short lines
    if re.search(r"\b(definition|glossary|appendix|table of)\b", lower):
        return "reference"

    return "explanation"


def chunk_section(
    section: Dict,
    document_name: str,
    min_tokens: int = 300,
    max_tokens: int = 800,
) -> List[Dict]:
    """
    Chunk a single section into 300–800 token chunks.

    Splits on paragraph boundaries first; only splits paragraphs if a
    single paragraph is too large. Never splits in the middle of a step
    or sentence.
    """
    body = section["body"]
    title = section["title"]

    # If the entire section fits in one chunk, return it as-is
    if count_tokens(body) <= max_tokens:
        return [_make_chunk(body, title, document_name)]

    # Split into paragraphs (and step lists stay together within a paragraph)
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

    chunks: List[str] = []
    buffer = ""

    for para in paragraphs:
        candidate = (buffer + "\n\n" + para).strip() if buffer else para
        cand_tokens = count_tokens(candidate)

        if cand_tokens <= max_tokens:
            buffer = candidate
        else:
            # Flush buffer if it has content
            if buffer:
                chunks.append(buffer)
                buffer = ""
            # If this paragraph alone exceeds max, split by sentence
            if count_tokens(para) > max_tokens:
                chunks.extend(_split_long_paragraph(para, max_tokens))
            else:
                buffer = para

    if buffer:
        chunks.append(buffer)

    # Merge small trailing chunks back into the previous one if possible
    chunks = _merge_small_chunks(chunks, min_tokens, max_tokens)

    return [_make_chunk(c, title, document_name) for c in chunks]


def _split_long_paragraph(para: str, max_tokens: int) -> List[str]:
    """Split an oversized paragraph on sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", para)
    result: List[str] = []
    buf = ""
    for s in sentences:
        candidate = (buf + " " + s).strip() if buf else s
        if count_tokens(candidate) <= max_tokens:
            buf = candidate
        else:
            if buf:
                result.append(buf)
            buf = s
    if buf:
        result.append(buf)
    return result


def _merge_small_chunks(chunks: List[str], min_tokens: int, max_tokens: int) -> List[str]:
    """Merge any chunks under min_tokens into the previous chunk if room allows."""
    if len(chunks) <= 1:
        return chunks

    merged = [chunks[0]]
    for c in chunks[1:]:
        if (count_tokens(c) < min_tokens
                and count_tokens(merged[-1] + "\n\n" + c) <= max_tokens):
            merged[-1] = merged[-1] + "\n\n" + c
        else:
            merged.append(c)
    return merged


def _make_chunk(text: str, section_title: str, document_name: str) -> Dict:
    return {
        "text": text,
        "metadata": {
            "document_name": document_name,
            "section_title": section_title,
            "content_type": detect_content_type(text),
            "token_count": count_tokens(text),
        },
    }


def chunk_document(
    cleaned_text: str,
    document_name: str,
    min_tokens: int = 300,
    max_tokens: int = 800,
) -> List[Dict]:
    """End-to-end: cleaned text -> list of chunk dicts with metadata."""
    sections = split_into_sections(cleaned_text)
    all_chunks: List[Dict] = []
    for section in sections:
        all_chunks.extend(
            chunk_section(section, document_name, min_tokens, max_tokens)
        )
    # Add a stable chunk_id
    for i, c in enumerate(all_chunks):
        c["metadata"]["chunk_id"] = f"{document_name}::chunk_{i}"
    return all_chunks