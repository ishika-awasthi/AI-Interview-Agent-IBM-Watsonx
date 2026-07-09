import re


def clean_response(text: str) -> str:
    """Clean model output by removing special chat tokens and extra blank lines."""
    # Remove special chat tokens e.g. <|assistant|>, <|user|>, <|system|>
    text = re.sub(r"<\|.*?\|>", "", text)

    # Collapse 3+ consecutive newlines down to two
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
