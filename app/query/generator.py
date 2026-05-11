"""LLM-based answer generation grounded in retrieved chunks."""
from typing import List, Dict
from anthropic import Anthropic

from app.config import settings
from app.query.classifier import QueryType


# --- System prompts per query type ---

SYSTEM_BASE = """You are a careful, source-grounded QA assistant. You answer ONLY using the provided context from the user's documents. You do not use outside knowledge.

Strict rules:
- If the answer is not contained in the context, reply exactly: "I don't know based on the provided documents."
- Always cite the document name and section for any fact you state.
- Do not invent details, examples, numbers, or names that are not in the context.
- Be concise. Avoid filler.
"""

SYSTEM_BY_TYPE = {
    "lookup": SYSTEM_BASE + """
For LOOKUP questions: give a short, direct answer (1–3 sentences). End with a "Source:" line citing document name and section.
""",
    "explanation": SYSTEM_BASE + """
For EXPLANATION questions: synthesize a clear, structured explanation in your own words, drawing only on the context. Use short paragraphs. End with a "Sources:" line listing document name and section(s).
""",
    "how_to": SYSTEM_BASE + """
For HOW-TO questions: produce a numbered, step-by-step procedure that uses ONLY the steps that appear in the context. Do not add steps the context doesn't support. If the context only partially covers the steps, say so explicitly. End with a "Source:" line citing document name and section.
""",
    "policy": SYSTEM_BASE + """
For POLICY/COMPLIANCE questions: be strict and precise. Quote or paraphrase the relevant rule directly from the context. Do not soften, generalize, or speculate. If the context does not clearly answer the question, reply: "I don't know based on the provided documents." End with a "Source:" line citing document name and section.
""",
}


# --- Data redirect (no LLM, no retrieval) ---

DATA_REDIRECT_MESSAGE = (
    "This looks like a data or analytics question (counts, rates, totals, "
    "averages, trends). I only answer questions that can be grounded in the "
    "uploaded documents. For metrics and aggregated data, please use your "
    "team's analytics dashboard, BI tool, or query the relevant database directly."
)


def build_context_block(chunks: List[Dict]) -> str:
    """Format retrieved chunks into a numbered context block for the LLM."""
    if not chunks:
        return "(no context retrieved)"
    parts = []
    for i, c in enumerate(chunks, start=1):
        meta = c["metadata"]
        parts.append(
            f"[Source {i}] Document: {meta.get('document_name', 'unknown')}\n"
            f"Section: {meta.get('section_title', 'unknown')}\n"
            f"Content type: {meta.get('content_type', 'unknown')}\n"
            f"---\n"
            f"{c['text']}"
        )
    return "\n\n".join(parts)


def build_user_prompt(query: str, context_block: str) -> str:
    return (
        f"CONTEXT FROM DOCUMENTS:\n"
        f"{context_block}\n\n"
        f"USER QUESTION:\n"
        f"{query}\n\n"
        f"Answer using ONLY the context above. If the answer isn't there, say "
        f"\"I don't know based on the provided documents.\""
    )


def generate_answer(query: str, query_type: QueryType, chunks: List[Dict]) -> str:
    """Call Claude with the appropriate system prompt and the retrieved context."""
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file."
        )

    if not chunks:
        return "I don't know based on the provided documents."

    client = Anthropic(api_key=settings.anthropic_api_key)

    system_prompt = SYSTEM_BY_TYPE.get(query_type, SYSTEM_BY_TYPE["lookup"])
    user_prompt = build_user_prompt(query, build_context_block(chunks))

    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,  # low temp for grounded, factual answers
    )

    # Claude returns content as a list of blocks; join the text blocks
    text_parts = [block.text for block in response.content if hasattr(block, "text")]
    return "".join(text_parts).strip()

COMPARISON_SYSTEM = """You are a careful, source-grounded comparison assistant. You compare how TWO documents address a question, using ONLY the provided context from each.

Strict rules:
- Use ONLY the context provided. No outside knowledge.
- If one or both documents don't address the question, say so explicitly.
- Structure your answer with clear sections for each document, then a synthesis.
- Cite document name and section for each fact.
- Be concise but thorough.

Format:
**[Document A name]**
[What this doc says, with section citations]

**[Document B name]**
[What this doc says, with section citations]

**Comparison**
[Key similarities and differences in 2-4 sentences]
"""


def generate_comparison(query, doc_a, chunks_a, doc_b, chunks_b):
    """Compare how two documents address a query."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    client = Anthropic(api_key=settings.anthropic_api_key)

    def fmt(chunks, label):
        if not chunks:
            return f"(No relevant content found in {label})"
        return "\n\n".join(
            f"[{label} - Section: {c['metadata'].get('section_title', 'unknown')}]\n{c['text']}"
            for c in chunks
        )

    user_prompt = (
        f"QUESTION: {query}\n\n"
        f"=== DOCUMENT A: {doc_a} ===\n"
        f"{fmt(chunks_a, doc_a)}\n\n"
        f"=== DOCUMENT B: {doc_b} ===\n"
        f"{fmt(chunks_b, doc_b)}\n\n"
        f"Compare how these two documents address the question above. "
        f"If a document doesn't address it, say so."
    )

    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=1500,
        system=COMPARISON_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.1,
    )

    text_parts = [b.text for b in response.content if hasattr(b, "text")]
    return "".join(text_parts).strip()