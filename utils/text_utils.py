"""
Shared text/feedback parsing helpers.

parse_feedback(), score_fraction(), and score_display() used to be defined
twice — once in app.py (Streamlit) and once, near-identically, inside
main.py's print_feedback() (CLI). Keeping one copy here means both
interfaces parse Granite's structured feedback text the same way, and a fix
to the parsing logic only has to be made once.
"""

import re

FEEDBACK_LABELS: list[str] = [
    "Overall Score", "Technical Accuracy", "Clarity", "Completeness",
    "Strengths", "Weaknesses", "Ideal Answer",
]


def clean_response(text: str) -> str:
    """Clean model output by removing special chat tokens and extra blank lines."""
    # Remove special chat tokens e.g. <|assistant|>, <|user|>, <|system|>
    text = re.sub(r"<\|.*?\|>", "", text)

    # Collapse 3+ consecutive newlines down to two
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_feedback(feedback: str) -> dict[str, str]:
    """Parse a structured feedback string into a label-to-value mapping.

    Scans each line for a known label prefix (e.g. ``"Overall Score:"``),
    collects the value that follows, and handles multi-line values by
    buffering continuation lines.

    Args:
        feedback: Raw text returned by the model after evaluation.

    Returns:
        A dict mapping each recognised label to its value string.
    """
    parsed: dict[str, str] = {}
    current_label: str | None = None
    buffer: list[str] = []
    for raw_line in feedback.splitlines():
        line = raw_line.strip()
        matched = False
        for lbl in FEEDBACK_LABELS:
            if line.lower().startswith(lbl.lower() + ":"):
                if current_label:
                    parsed[current_label] = " ".join(buffer).strip()
                current_label = lbl
                buffer = [line[len(lbl) + 1:].strip()]
                matched = True
                break
        if not matched and current_label and line:
            buffer.append(line)
    if current_label:
        parsed[current_label] = " ".join(buffer).strip()
    return parsed


def score_fraction(value: str) -> float:
    """Convert a score string such as ``'8/10'`` to a fraction in [0, 1].

    Accepts formats like ``'8/10'``, ``'8'``, or ``'8.5 / 10'``.
    Returns ``0.0`` when the string cannot be parsed.
    Assumes a denominator of 10 when none is present.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?", value or "")
    if not match:
        return 0.0
    num = float(match.group(1))
    denom = float(match.group(2)) if match.group(2) else 10.0
    return max(0.0, min(1.0, num / denom)) if denom else 0.0


def score_display(value: str) -> str:
    """Extract a short 'N/10'-style label from a score string for compact display.

    Model output for a score field sometimes includes trailing rationale text
    on the same line (e.g. ``'6/10 The candidate correctly identifies...'``).
    This pulls out just the leading numeric score/denominator so UI elements
    like the score ring never have to render a full sentence. Falls back to
    '—' when no numeric score can be found.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?))?", value or "")
    if not match:
        return "—"
    num = match.group(1)
    denom = match.group(2) or "10"
    return f"{num}/{denom}"
