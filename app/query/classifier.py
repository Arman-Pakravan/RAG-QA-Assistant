"""Hybrid query classifier: rules first, LLM fallback for ambiguity."""
import re
from typing import Literal

from anthropic import Anthropic
from app.config import settings

QueryType = Literal["lookup", "explanation", "how_to", "policy", "data"]


# --- Strong rule-based signals (high confidence) ---

# Data: stats/aggregations — should always short-circuit retrieval
DATA_PATTERNS = [
    r"\bhow many\b",
    r"\bhow much\b",
    r"\bwhat (?:is the |'s the )?(?:count|total|number|sum|average|avg|mean|median)\b",
    r"\b(?:count|total|number|sum) of\b",
    r"\b(?:rate|percentage|percent|%) of\b",
    r"\bwhat (?:percentage|percent|%)\b",
    r"\baverage (?:rate|number|count|time|duration)\b",
    r"\b(?:trend|trends) (?:over|in|for)\b",
    r"\bbreakdown of\b",
    r"\b(?:metric|metrics|kpi|kpis)\b",
]

# How-to: explicit procedural language
HOW_TO_STRONG_PATTERNS = [
    r"\bhow (?:do|can|should) (?:i|we|you|one)\b",
    r"\bhow to\b",
    r"\bsteps? (?:to|for)\b",
    r"\bwalk me through\b",
    r"\bwhat (?:is|are) the steps?\b",
    r"\binstructions? (?:to|for)\b",
]

# Policy: explicit compliance/rule language
POLICY_STRONG_PATTERNS = [
    r"\b(?:am i|are we|is it) (?:allowed|permitted|required|prohibited)\b",
    r"\bwhat (?:is|are) the (?:policy|policies|rule|rules|requirement|requirements)\b",
    r"\bcompliance\b",
    r"\bpolicy on\b",
    r"\bregulation(?:s)?\b",
    r"\b(?:permitted|forbidden|mandatory)\b",
]


def _matches_any(text: str, patterns) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _llm_classify(query: str) -> QueryType:
    """Fallback to Claude for ambiguous queries."""
    if not settings.anthropic_api_key:
        return "lookup"  # safe default

    client = Anthropic(api_key=settings.anthropic_api_key)

    system = """You classify user queries into exactly one category. Reply with only the category name, nothing else.

Categories:
- lookup: a direct factual question seeking specific information ("what is X", "who did X", "summarize X")
- explanation: asks for understanding, reasoning, comparison, or synthesis ("why", "how does X work", "compare X and Y", "explain X", or open-ended requests like "give me feedback on X" or "what could be improved")
- how_to: asks for procedural step-by-step instructions to do something
- policy: asks about rules, compliance, what is allowed/required/prohibited
- data: asks for counts, totals, rates, percentages, metrics, or aggregated statistics"""

    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=10,
        system=system,
        messages=[{"role": "user", "content": f"Query: {query}\n\nCategory:"}],
        temperature=0.0,
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text")).strip().lower()

    # Validate and fall back to lookup if Claude returns something unexpected
    valid = {"lookup", "explanation", "how_to", "policy", "data"}
    return text if text in valid else "lookup"


def classify_query(query: str) -> QueryType:
    """
    Hybrid classification:
      1. Strong rule patterns first (free, instant, high precision)
      2. Claude fallback for everything else (more accurate on ambiguous queries)
    """
    q = query.strip().lower()

    # Strong rule matches — confident enough to skip the LLM
    if _matches_any(q, DATA_PATTERNS):
        return "data"
    if _matches_any(q, HOW_TO_STRONG_PATTERNS):
        return "how_to"
    if _matches_any(q, POLICY_STRONG_PATTERNS):
        return "policy"

    # Ambiguous — let Claude decide
    try:
        return _llm_classify(query)
    except Exception:
        return "lookup"  # safe fallback if LLM is unavailable